package dev.eziedutech.dcai.guardian.service

import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.util.Log
import dev.eziedutech.dcai.guardian.BuildConfig
import dev.eziedutech.dcai.guardian.ServiceLocator
import dev.eziedutech.dcai.guardian.net.BackendClient
import dev.eziedutech.dcai.guardian.net.DeviceRevokedException
import dev.eziedutech.dcai.guardian.screen.ScreenGuard
import dev.eziedutech.dcai.guardian.sites.SiteGuardVpn
import dev.eziedutech.dcai.guardian.sites.SiteLists
import dev.eziedutech.dcai.guardian.vision.ThreadLevels
import android.net.VpnService
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.serialization.json.jsonPrimitive
import okhttp3.sse.EventSource
import kotlin.coroutines.resume

/**
 * Keeps dcAI active and visible. While it runs, the child sees a persistent notification.
 * It follows the live stream for nudges, sends a heartbeat so the parent's dashboard knows
 * the phone is protected, and stops itself if the parent revokes the device.
 *
 * There is no hidden mode: the only way the notification goes away is the service stopping.
 */
class GuardianService : Service() {
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(dev.eziedutech.dcai.guardian.ui.localizedService(newBase))
    }

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val store = ServiceLocator.store(this)
        if (!store.isPaired || !store.setupDone) {
            stopSelf()
            return START_NOT_STICKY
        }
        Notifications.ensureChannels(this)
        startForegroundCompat()
        if (!started) {
            started = true
            scope.launch { streamLoop() }
            scope.launch { heartbeatLoop() }
            scope.launch { screenLoop() }
        }
        return START_STICKY
    }

    private var started = false

    private fun startForegroundCompat() {
        val nickname = ServiceLocator.store(this).config?.childNickname
        val notification = Notifications.statusNotification(this, nickname)
        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(Notifications.STATUS_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        } else {
            startForeground(Notifications.STATUS_ID, notification)
        }
    }

    private suspend fun streamLoop() {
        val client = ServiceLocator.client(this) ?: return
        while (scope.isActive) {
            val closeCode = awaitStream(client)
            if (closeCode == 401) {
                onRevoked()
                return
            }
            delay(3000) // the backend closes streams periodically on purpose; reconnect
        }
    }

    /** Opens one stream and suspends until it closes; returns the HTTP code of a failure. */
    private suspend fun awaitStream(client: BackendClient): Int? = suspendCancellableCoroutine { cont ->
        var source: EventSource? = null
        source = client.openStream(
            lastEventId = null,
            onEvent = { event -> scope.launch { handle(event.event, event.data) } },
            onClosed = { code -> if (cont.isActive) cont.resume(code) },
        )
        cont.invokeOnCancellation { source?.cancel() }
    }

    private fun handle(event: String, data: kotlinx.serialization.json.JsonObject) {
        when (event) {
            "nudge" -> data["child_nudge"]?.jsonPrimitive?.content?.let {
                ServiceLocator.store(this).addNudge(it)
                Notifications.showNudge(this, it)
            }
            "config" -> runCatching { scope.launch { refreshConfig() } }
            "time_decision" -> {
                val approved = data["approved"]?.jsonPrimitive?.content == "true"
                val minutes = data["minutes"]?.jsonPrimitive?.content?.toIntOrNull() ?: 0
                val store = ServiceLocator.store(this)
                if (data["request_id"]?.jsonPrimitive?.content == store.pendingTimeRequest) store.pendingTimeRequest = null
                if (approved && minutes > 0) screenGuard.onApproved(minutes)
                Notifications.showTimeDecision(this, approved, minutes)
                ScreenGuard.decisions.value++
            }
            "revoked" -> onRevoked()
            // A received image is only looked at in a conversation at perhatian or above.
            "level" -> {
                val key = data["thread_key"]?.jsonPrimitive?.content
                val level = data["level"]?.jsonPrimitive?.content
                if (key != null && level != null) ThreadLevels.update(key, level)
            }
        }
    }

    private suspend fun refreshConfig() {
        val client = ServiceLocator.client(this) ?: return
        runCatching { ServiceLocator.store(this).config = client.config() }
        applySites()
    }

    /** Site protection follows consent: it stops when the parent withdraws the scope, and
     * comes back after a restart if it was on and the VPN permission is still granted. */
    private fun applySites() {
        val store = ServiceLocator.store(this)
        val allowed = store.config?.has("domain") == true
        when {
            !allowed && SiteGuardVpn.running -> SiteGuardVpn.stop(this)
            allowed && store.sitesEnabled && !SiteGuardVpn.running && VpnService.prepare(this) == null ->
                SiteGuardVpn.start(this)
        }
    }

    private val screenGuard by lazy { ScreenGuard(this) }

    /** Time online checks, every two seconds while dcAI runs. */
    private suspend fun screenLoop() {
        while (scope.isActive) {
            try {
                kotlinx.coroutines.withContext(Dispatchers.IO) { screenGuard.tick() }
            } catch (e: Exception) {
                Log.d(TAG, "screen check failed: ${e.javaClass.simpleName}")
            }
            delay(2000)
        }
    }

    private suspend fun heartbeatLoop() {
        val client = ServiceLocator.client(this) ?: return
        while (scope.isActive) {
            try {
                val config = client.heartbeat(BuildConfig.VERSION_NAME, DeviceState.services(this))
                ServiceLocator.store(this).config = config
                applySites()
            } catch (_: DeviceRevokedException) {
                onRevoked()
                return
            } catch (e: Exception) {
                Log.d(TAG, "heartbeat failed: ${e.javaClass.simpleName}")
            }
            delay(60_000)
        }
    }

    private fun onRevoked() {
        SiteGuardVpn.stop(this)
        ServiceLocator.client(this)?.let { SiteLists(this, it).clear() }
        ServiceLocator.store(this).clear()
        ServiceLocator.reset()
        ThreadLevels.clear()
        stopSelf()
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    companion object {
        private const val TAG = "dcai.service"

        fun start(context: Context) {
            val intent = Intent(context, GuardianService::class.java)
            context.startForegroundService(intent)
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, GuardianService::class.java))
        }
    }
}
