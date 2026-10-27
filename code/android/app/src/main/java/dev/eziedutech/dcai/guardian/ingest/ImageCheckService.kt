package dev.eziedutech.dcai.guardian.ingest

import android.app.Service
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.Message
import android.os.Messenger
import android.util.Log
import dev.eziedutech.dcai.guardian.ServiceLocator
import dev.eziedutech.dcai.guardian.vision.Bitmaps
import dev.eziedutech.dcai.guardian.vision.Decision
import dev.eziedutech.dcai.guardian.vision.ImageContext
import dev.eziedutech.dcai.guardian.vision.Trigger
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * How an app that integrated dcAI asks whether to blur an image before it shows or sends
 * it. The app binds with the signature-level INGEST permission, grants read access to the
 * image's content URI, and gets back the decision: blur everything, blur some regions, or
 * leave it. The image is read in memory and never stored or sent by dcAI.
 */
class ImageCheckService : Service() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    private val messenger by lazy {
        Messenger(
            object : Handler(Looper.getMainLooper()) {
                override fun handleMessage(msg: Message) {
                    if (msg.what != MSG_CHECK) return
                    val replyTo = msg.replyTo ?: return
                    val request = Bundle(msg.data)
                    val requestId = msg.arg1
                    scope.launch { replyTo.send(reply(requestId, check(request))) }
                }
            },
        )
    }

    override fun onBind(intent: Intent?): IBinder = messenger.binder

    private suspend fun check(data: Bundle): Decision {
        val uri = data.getString(KEY_URI)?.let(Uri::parse) ?: return Decision.leave()
        val trigger = Trigger.entries.firstOrNull { it.wire == data.getString(KEY_TRIGGER) } ?: return Decision.leave()
        val guard = ServiceLocator.imageGuard(applicationContext) ?: return Decision.leave().also { Log.d(TAG, "not paired") }
        return try {
            val bitmap = withContext(Dispatchers.IO) { Bitmaps.decode(contentResolver, uri) } ?: return Decision.leave().also { Log.d(TAG, "unreadable image") }
            try {
                guard.check(
                    bitmap,
                    ImageContext(
                        trigger = trigger,
                        threadId = data.getString(KEY_THREAD) ?: "default",
                        appPackage = data.getString(KEY_APP) ?: "unknown.app",
                        channel = data.getString(KEY_CHANNEL) ?: "dm",
                        sender = data.getString(KEY_SENDER) ?: "contact",
                        contactKnown = data.getBoolean(KEY_CONTACT_KNOWN, false),
                    ),
                )
            } finally {
                bitmap.recycle()
            }
        } catch (e: Exception) {
            // Type only: a message could carry a path or a detail of the image.
            Log.d(TAG, "image check failed: ${e.javaClass.simpleName}")
            Decision.leave()
        }
    }

    private fun reply(requestId: Int, d: Decision): Message = Message.obtain(null, MSG_RESULT, requestId, 0).apply {
        data = Bundle().apply {
            putString(KEY_ACTION, d.action.wire)
            putString(KEY_CATEGORY, d.category.wire)
            putInt(KEY_SCORE, d.score)
            putString(KEY_MODEL_VERSION, d.modelVersion)
            putBoolean(KEY_BLUR_ALL, d.blurAll)
            putFloatArray(KEY_REGIONS, d.regions.flatMap { listOf(it.left, it.top, it.right, it.bottom) }.toFloatArray())
        }
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    companion object {
        private const val TAG = "dcai.imagecheck"
        const val MSG_CHECK = 1
        const val MSG_RESULT = 2

        const val KEY_URI = "uri"
        const val KEY_TRIGGER = "trigger"
        const val KEY_THREAD = "thread"
        const val KEY_APP = "app"
        const val KEY_CHANNEL = "channel"
        const val KEY_SENDER = "sender"
        const val KEY_CONTACT_KNOWN = "contact_known"

        const val KEY_ACTION = "action"
        const val KEY_CATEGORY = "category"
        const val KEY_SCORE = "score"
        const val KEY_MODEL_VERSION = "model_version"
        const val KEY_BLUR_ALL = "blur_all"
        /** left, top, right, bottom of each region, as fractions of the image. */
        const val KEY_REGIONS = "regions"
    }
}
