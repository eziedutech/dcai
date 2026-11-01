package dev.eziedutech.dcai.guardian.ingest

import android.content.Context
import android.util.Log
import kotlinx.coroutines.withTimeout

/**
 * The real on-device stage 1 analyzer: the distilled Llama student under ExecuTorch. It labels
 * one masked message so ordinary chat can be judged and dropped locally, and only flagged
 * messages are sent to the server (see MessageIngest).
 *
 * The model runs in a separate :ondevice process reached through [OnDeviceModelClient]; this
 * class builds the prompt, runs it there, and parses the result. If anything fails, including the
 * model process being killed for memory or taking too long, it returns null and the caller sends
 * the message online (fail safe). Nothing here can crash the dcAI UI or services.
 */
class ExecuTorchStage1Analyzer(
    private val context: Context,
    private val client: OnDeviceModelClient,
) : OnDeviceAnalyzer {

    override val installed: Boolean
        get() = OnDeviceFiles.installed(context)

    override suspend fun label(sender: String, maskedText: String): OnDeviceResult? {
        if (!installed) return null
        val prompt = Stage1Prompt.build(sender, maskedText)
        val raw = try {
            withTimeout(GENERATE_TIMEOUT_MS) { client.generate(prompt) }
        } catch (t: Throwable) {
            // Never log the prompt or output, only the failure type. A timeout here usually means
            // the :ondevice process was killed for memory mid-run; fall back to online.
            Log.w(TAG, "ondevice label failed: ${t.javaClass.simpleName}")
            return null
        }
        val parsed = Stage1Prompt.parse(raw) ?: return null
        val labels = Stage1Prompt.applyRules(
            sender, parsed.labels, Stage1Prompt.hasFindings(maskedText),
        )
        return OnDeviceResult(labels.toList(), parsed.signal)
    }

    private companion object {
        const val TAG = "dcai.ondevice"
        // First message loads the model and evaluates the full prompt; generous, but bounded so a
        // killed or hung model process cannot stall ingest forever.
        const val GENERATE_TIMEOUT_MS = 60_000L
    }
}
