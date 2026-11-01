package dev.eziedutech.dcai.guardian.ingest

import android.util.Log

/**
 * The real on-device stage 1 analyzer: the distilled Llama 3.2 3B student running under
 * ExecuTorch on the phone. It labels one masked message so ordinary chat can be judged and
 * dropped locally, and only flagged messages are sent to the server (see MessageIngest).
 *
 * The prompt, parsing and rules are in Stage1Prompt (ported from the server's stage 1); the
 * runtime and model lifecycle are in OnDeviceModel. This class only joins them. If anything
 * fails it returns null, and the caller sends the message to fail safe.
 */
class ExecuTorchStage1Analyzer(private val model: OnDeviceModel) : OnDeviceAnalyzer {

    override val installed: Boolean
        get() = model.installed

    override suspend fun label(sender: String, maskedText: String): OnDeviceResult? {
        if (!installed) return null
        val prompt = Stage1Prompt.build(sender, maskedText)
        val raw = try {
            model.generate(prompt)
        } catch (t: Throwable) {
            // Never log the prompt or output, only the failure type.
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
    }
}
