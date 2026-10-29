package dev.eziedutech.dcai.guardian.ingest

import android.accessibilityservice.AccessibilityService
import android.content.ComponentName
import android.content.Context
import android.graphics.Bitmap
import android.os.SystemClock
import android.provider.Settings
import android.util.Log
import android.view.Display
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import dev.eziedutech.dcai.guardian.R
import dev.eziedutech.dcai.guardian.ServiceLocator
import dev.eziedutech.dcai.guardian.service.Notifications
import dev.eziedutech.dcai.guardian.vision.ImageContext
import dev.eziedutech.dcai.guardian.vision.ThreadLevels
import dev.eziedutech.dcai.guardian.vision.Trigger
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

/**
 * The screen-text source agreed in proposal 0002: dcAI reads the text shown on screen in any
 * app, so patterns are recognised whatever app the child chats in, and whatever keyboard they
 * use. This is the primary source; the dcAI keyboard and the chat-notification listener stay
 * as complements. It runs only while the parent grants the "layar" scope, the child sees dcAI
 * in Android's accessibility list, and the "dcAI aktif" notification stays visible: there is
 * no hidden mode.
 *
 * What leaves the phone is the same as every other source: [MessageIngest] masks the text
 * here, and only flagged, masked messages are sent. When a conversation is already risky, a
 * screenshot is judged on the phone through the existing vision pipeline; the screenshot is
 * never sent.
 */
class ScreenReaderService : AccessibilityService() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private val screen = ScreenText()
    private var lastShot = 0L

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        event ?: return
        val store = ServiceLocator.store(this)
        if (store.config?.has("layar") != true) return
        val pkg = event.packageName?.toString() ?: return
        if (pkg == packageName || ScreenText.isNoiseApp(pkg)) return

        val root = rootInActiveWindow ?: return
        val collected = collect(root)
        val thread = collected.title ?: pkg
        RecentThreads.note(pkg, thread)

        // Outgoing: the child's own typing, taken when the field is cleared on send. This is
        // what the dcAI keyboard alone cannot give: it works with any keyboard.
        screen.onEditable(pkg, collected.editable.orEmpty())?.let { sent ->
            submit(thread, pkg, sender = "child", raw = sent)
        }

        // Incoming/transcript: only when a compose field is on screen (a messaging surface),
        // to keep ordinary app chrome out. New visible lines, minus the field's own text.
        if (collected.editable != null) {
            val field = collected.editable.trim()
            val lines = collected.lines.filter { it.trim() != field }
            for (line in screen.newLines(pkg, thread, lines)) {
                submit(thread, pkg, sender = "contact", raw = line)
            }
            maybeScreenshot(pkg, thread)
        }
    }

    private fun submit(thread: String, pkg: String, sender: String, raw: String) {
        val ingest = ServiceLocator.ingest(this) ?: return
        scope.launch {
            runCatching {
                ingest.submit(
                    threadId = thread,
                    appPackage = pkg,
                    channel = "dm",
                    contactKnown = false,
                    sender = sender,
                    rawText = raw,
                )
            }.onFailure { Log.d(TAG, "screen submit failed: ${it.javaClass.simpleName}") }
        }
    }

    /** One text buffer the child is editing, plus the other text lines on screen and a title. */
    private class Collected(val editable: String?, val lines: List<String>, val title: String?)

    private fun collect(root: AccessibilityNodeInfo): Collected {
        var editable: String? = null
        val lines = ArrayList<String>()
        val stack = ArrayDeque<AccessibilityNodeInfo>()
        stack.addLast(root)
        var budget = 600
        while (stack.isNotEmpty() && budget-- > 0) {
            val node = stack.removeLast()
            val t = node.text?.toString()?.trim()
            if (!t.isNullOrEmpty()) {
                if (node.isEditable) {
                    if (editable == null) editable = t
                } else {
                    lines.add(t)
                }
            }
            for (i in 0 until node.childCount) node.getChild(i)?.let { stack.addLast(it) }
        }
        val title = root.paneTitle?.toString()?.trim()?.takeIf { it.isNotEmpty() }
        return Collected(editable, lines, title)
    }

    /**
     * In a conversation already at perhatian or above, judge a screenshot on the phone through
     * the same vision pipeline the chat-SDK path uses. The bitmap never leaves the phone and is
     * recycled straight after. A sensitive result shows the child a reminder.
     */
    private fun maybeScreenshot(pkg: String, thread: String) {
        val store = ServiceLocator.store(this)
        if (store.config?.has("gambar") != true) return
        if (!ThreadLevels.atLeast(threadKey(pkg, thread), "perhatian")) return
        val now = SystemClock.elapsedRealtime()
        if (now - lastShot < SHOT_INTERVAL_MS) return
        lastShot = now
        takeScreenshot(
            Display.DEFAULT_DISPLAY,
            mainExecutor,
            object : TakeScreenshotCallback {
                override fun onSuccess(result: ScreenshotResult) {
                    val bitmap = toBitmap(result)
                    if (bitmap == null) return
                    scope.launch {
                        try {
                            val guard = ServiceLocator.imageGuard(this@ScreenReaderService) ?: return@launch
                            val decision = guard.check(
                                bitmap,
                                ImageContext(Trigger.PERCAKAPAN, thread, pkg, "dm", "contact", false),
                            )
                            if (decision.blurAll) {
                                Notifications.showNudge(
                                    this@ScreenReaderService,
                                    getString(R.string.screen_sensitive_nudge),
                                )
                            }
                        } finally {
                            bitmap.recycle()
                        }
                    }
                }

                override fun onFailure(errorCode: Int) {
                    Log.d(TAG, "screenshot failed: $errorCode")
                }
            },
        )
    }

    /** A screenshot result into a software bitmap the detectors can read; buffer is closed. */
    private fun toBitmap(result: ScreenshotResult): Bitmap? {
        val buffer = result.hardwareBuffer
        return try {
            val hardware = Bitmap.wrapHardwareBuffer(buffer, result.colorSpace) ?: return null
            val software = hardware.copy(Bitmap.Config.ARGB_8888, false)
            hardware.recycle()
            software
        } catch (e: Exception) {
            Log.d(TAG, "screenshot decode failed: ${e.javaClass.simpleName}")
            null
        } finally {
            buffer.close()
        }
    }

    override fun onInterrupt() {}

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    companion object {
        private const val TAG = "dcai.screen"
        private const val SHOT_INTERVAL_MS = 15_000L

        /** Whether the parent turned on the dcAI accessibility service in Android's settings. */
        fun enabled(context: Context): Boolean {
            val flat = Settings.Secure.getString(
                context.contentResolver,
                Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES,
            ) ?: return false
            val me = ComponentName(context, ScreenReaderService::class.java)
            return flat.split(":").any { ComponentName.unflattenFromString(it) == me }
        }
    }
}
