package dev.eziedutech.dcai.guardian.vision

import android.graphics.Bitmap
import android.util.Log
import dev.eziedutech.dcai.guardian.data.GuardianStore
import dev.eziedutech.dcai.guardian.ingest.MessageIngest
import dev.eziedutech.dcai.guardian.ingest.threadKey
import dev.eziedutech.dcai.guardian.net.BackendClient
import dev.eziedutech.dcai.guardian.net.ImageSignalRequest
import dev.eziedutech.dcai.guardian.net.brief
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/** Where an image came from, as the chat app reports it. */
data class ImageContext(
    val trigger: Trigger,
    val threadId: String,
    val appPackage: String,
    val channel: String,
    val sender: String,
    val contactKnown: Boolean,
    /** Read from another app's screen: dcAI cannot blur it there, only remind the child. */
    val shownByOtherApp: Boolean = false,
    /** A video's cover read from another app's screen: reported as a video. */
    val video: Boolean = false,
)

/**
 * One image, judged on the phone. The bitmap stays in memory and is never sent. What may
 * leave: the label (category, action, score, model) and, for a received image in a risky
 * chat, the image's text after masking, assessed like a message.
 */
class ImageGuard(
    private val store: GuardianStore,
    private val client: BackendClient,
    private val ingest: MessageIngest,
    private val detectors: OnDeviceDetectors,
    private val videoModel: VideoModel,
) {
    /** Whether this image or video is checked at all: the gambar scope, and for a received
     * one, a chat already at perhatian or above. */
    private fun wanted(context: ImageContext): Boolean {
        val config = store.config ?: return false
        if (!config.has("gambar")) return false
        val key = threadKey(context.appPackage, context.threadId)
        return context.trigger != Trigger.PERCAKAPAN || ThreadLevels.atLeast(key, "perhatian")
    }

    /** How many frames to take from a video: what the video model reads, else a few for the
     * image model. */
    val videoFrames: Int get() = if (videoModel.installed) videoModel.frames else VideoPolicy.IMAGE_FRAMES

    suspend fun check(bitmap: Bitmap, context: ImageContext): Decision = withContext(Dispatchers.Default) {
        if (!wanted(context)) return@withContext Decision.leave()
        val config = store.config ?: return@withContext Decision.leave()
        val key = threadKey(context.appPackage, context.threadId)

        val names = listOf(config.childNickname).filter { it.isNotBlank() }
        val result = detectors.run(bitmap, names, wantFaces = context.trigger == Trigger.DIBAGIKAN)
        val hash = Bitmaps.dHash(bitmap)
        val decided = ImagePolicy.decide(
            context.trigger,
            result.findings,
            thresholds = store.thresholds(),
            confirmedFalse = LocalTuning.matches(hash, store.confirmedFalse()),
        )
        // On another app's screen the picture stays visible, so it is reported as a reminder,
        // and a picture still on screen at the next screenshot is reported only once.
        val decision = when {
            !context.shownByOtherApp || !decided.signal -> decided
            !RecentImages.firstTime(key, hash, System.currentTimeMillis()) -> return@withContext decided.copy(repeat = true)
            decided.action == Action.DIKABURKAN -> decided.copy(action = Action.DIINGATKAN)
            else -> decided
        }

        // Counts and labels only; never text or pixels.
        Log.d(TAG, "image judged trigger=${context.trigger.wire} category=${decision.category.wire} text_blocks=${result.blocks.size} faces=${result.findings.faces.size}")
        val sent = report(decision, key, context, if (context.video) MEDIA_VIDEO else MEDIA_IMAGE)
        // Not reported after all: the next screenshot of the same picture tries again.
        if (!sent && context.shownByOtherApp && decision.signal) RecentImages.forget(key, hash)

        if (context.trigger == Trigger.PERCAKAPAN) {
            val text = OcrText.joined(result.blocks)
            if (text.isNotEmpty()) {
                runCatching {
                    ingest.submit(
                        threadId = context.threadId,
                        appPackage = context.appPackage,
                        channel = context.channel,
                        contactKnown = context.contactKnown,
                        sender = context.sender,
                        rawText = text,
                    )
                }.onFailure { Log.d(TAG, "image text failed: ${it.brief()}") }
            }
        }
        decision
    }

    /**
     * A video, judged from frames taken on the phone ([VideoFrames]). The image model reads up
     * to [VideoPolicy.IMAGE_FRAMES] of them and stops at the first sensitive one; the video
     * model, when installed, reads them all. Faces and text are not looked for in a video.
     */
    suspend fun checkVideo(frames: List<Bitmap>, context: ImageContext): Decision = withContext(Dispatchers.Default) {
        if (frames.isEmpty() || !wanted(context)) return@withContext Decision.leave()
        val key = threadKey(context.appPackage, context.threadId)
        val thresholds = store.thresholds()

        val scores = mutableListOf<SensitiveScore?>()
        for (i in VideoPolicy.spread(frames.size, VideoPolicy.IMAGE_FRAMES)) {
            val s = detectors.sensitiveScore(frames[i])
            scores += s
            if (VideoPolicy.over(s, thresholds)) break
        }
        if (scores.none { VideoPolicy.over(it, thresholds) } && videoModel.installed) {
            scores += videoModel.score(frames)
        }
        val hash = Bitmaps.dHash(frames[frames.size / 2])
        val decision = ImagePolicy.decide(
            context.trigger,
            Findings(sensitive = VideoPolicy.top(scores, thresholds)),
            thresholds = thresholds,
            confirmedFalse = LocalTuning.matches(hash, store.confirmedFalse()),
        )
        // Counts and labels only.
        Log.d(TAG, "video judged trigger=${context.trigger.wire} category=${decision.category.wire} frames=${frames.size} scored=${scores.size}")
        report(decision, key, context, MEDIA_VIDEO)
        decision
    }

    /** Sends the label of a non-safe decision; false when that failed. */
    private suspend fun report(decision: Decision, key: String, context: ImageContext, media: String): Boolean {
        if (!decision.signal) return true
        return runCatching {
            client.sendImageSignal(
                ImageSignalRequest(
                    threadKey = key,
                    trigger = context.trigger.wire,
                    sender = context.sender,
                    category = decision.category.wire,
                    action = decision.action.wire,
                    score = decision.score,
                    modelVersion = decision.modelVersion,
                    media = media,
                ),
            )
        }.onFailure { Log.d(TAG, "image signal failed: ${it.brief()}") }.isSuccess
    }

    private companion object {
        const val TAG = "dcai.vision"
        const val MEDIA_IMAGE = "gambar"
        const val MEDIA_VIDEO = "video"
    }
}
