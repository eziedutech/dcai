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
import dev.eziedutech.dcai.guardian.BuildConfig
import dev.eziedutech.dcai.guardian.ServiceLocator
import dev.eziedutech.dcai.guardian.vision.Bitmaps
import dev.eziedutech.dcai.guardian.vision.Decision
import dev.eziedutech.dcai.guardian.vision.ImageContext
import dev.eziedutech.dcai.guardian.vision.Trigger
import dev.eziedutech.dcai.guardian.vision.VideoFrames
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
 *
 * A video (media = "video") is judged from frames taken in memory; the app gets the same
 * kind of decision for the whole clip. Builds without [BuildConfig.VIDEO_CHECK] leave videos
 * alone.
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
        val context = ImageContext(
            trigger = trigger,
            threadId = data.getString(KEY_THREAD) ?: "default",
            appPackage = data.getString(KEY_APP) ?: "unknown.app",
            channel = data.getString(KEY_CHANNEL) ?: "dm",
            sender = data.getString(KEY_SENDER) ?: "contact",
            contactKnown = data.getBoolean(KEY_CONTACT_KNOWN, false),
        )
        if (data.getString(KEY_MEDIA) == MEDIA_VIDEO) return checkVideo(uri, context)
        return try {
            val bitmap = withContext(Dispatchers.IO) { Bitmaps.decode(contentResolver, uri) } ?: return Decision.leave().also { Log.d(TAG, "unreadable image") }
            try {
                guard.check(bitmap, context)
            } finally {
                bitmap.recycle()
            }
        } catch (e: Exception) {
            // Type only: a message could carry a path or a detail of the image.
            Log.d(TAG, "image check failed: ${e.javaClass.simpleName}")
            Decision.leave()
        }
    }

    private suspend fun checkVideo(uri: Uri, context: ImageContext): Decision {
        if (!BuildConfig.VIDEO_CHECK) return Decision.leave().also { Log.d(TAG, "video checks off in this build") }
        val guard = ServiceLocator.imageGuard(applicationContext) ?: return Decision.leave()
        return try {
            val frames = withContext(Dispatchers.IO) { VideoFrames.extract(applicationContext, uri, guard.videoFrames) }
            try {
                guard.checkVideo(frames, context)
            } finally {
                frames.forEach { it.recycle() }
            }
        } catch (e: Exception) {
            Log.d(TAG, "video check failed: ${e.javaClass.simpleName}")
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
        /** "gambar" (default) or "video". */
        const val KEY_MEDIA = "media"
        const val MEDIA_VIDEO = "video"

        const val KEY_ACTION = "action"
        const val KEY_CATEGORY = "category"
        const val KEY_SCORE = "score"
        const val KEY_MODEL_VERSION = "model_version"
        const val KEY_BLUR_ALL = "blur_all"
        /** left, top, right, bottom of each region, as fractions of the image. */
        const val KEY_REGIONS = "regions"
    }
}
