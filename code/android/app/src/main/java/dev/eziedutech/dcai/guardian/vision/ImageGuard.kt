package dev.eziedutech.dcai.guardian.vision

import android.graphics.Bitmap
import android.util.Log
import dev.eziedutech.dcai.guardian.data.GuardianStore
import dev.eziedutech.dcai.guardian.ingest.MessageIngest
import dev.eziedutech.dcai.guardian.ingest.threadKey
import dev.eziedutech.dcai.guardian.net.BackendClient
import dev.eziedutech.dcai.guardian.net.ImageSignalRequest
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
) {
    suspend fun check(bitmap: Bitmap, context: ImageContext): Decision = withContext(Dispatchers.Default) {
        val config = store.config ?: return@withContext Decision.leave()
        if (!config.has("gambar")) return@withContext Decision.leave()
        val key = threadKey(context.appPackage, context.threadId)
        if (context.trigger == Trigger.PERCAKAPAN && !ThreadLevels.atLeast(key, "perhatian")) {
            return@withContext Decision.leave()
        }

        val names = listOf(config.childNickname).filter { it.isNotBlank() }
        val result = detectors.run(bitmap, names, wantFaces = context.trigger == Trigger.DIBAGIKAN)
        val hash = Bitmaps.dHash(bitmap)
        val decision = ImagePolicy.decide(
            context.trigger,
            result.findings,
            thresholds = store.thresholds(),
            confirmedFalse = LocalTuning.matches(hash, store.confirmedFalse()),
        )

        // Counts and labels only; never text or pixels.
        Log.d(TAG, "image judged trigger=${context.trigger.wire} category=${decision.category.wire} text_blocks=${result.blocks.size} faces=${result.findings.faces.size}")
        if (decision.signal) {
            runCatching {
                client.sendImageSignal(
                    ImageSignalRequest(
                        threadKey = key,
                        trigger = context.trigger.wire,
                        sender = context.sender,
                        category = decision.category.wire,
                        action = decision.action.wire,
                        score = decision.score,
                        modelVersion = decision.modelVersion,
                    ),
                )
            }.onFailure { Log.d(TAG, "image signal failed: ${it.javaClass.simpleName}") }
        }

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
                }.onFailure { Log.d(TAG, "image text failed: ${it.javaClass.simpleName}") }
            }
        }
        decision
    }

    private companion object {
        const val TAG = "dcai.vision"
    }
}
