package dev.eziedutech.dcai.guardian.ingest

/**
 * The slot for an on-device stage 1 analyzer (the "Llama di ponsel" mode). It labels one
 * masked message on the phone so ordinary messages can be judged and dropped locally, and
 * only flagged ones are sent to the server.
 *
 * No model ships with this build. A model is plugged in by implementing this interface with
 * an ExecuTorch runner over the exported .pte and registering it in ServiceLocator. Until
 * then installed is false and every message goes to the server (the online Muse Spark path),
 * so the default behaviour is unchanged. Mirrors vision.SensitiveModel: an interface with a
 * no-op default, so the dispatch seam exists before the runtime does.
 */
interface OnDeviceAnalyzer {
    val installed: Boolean

    /** Labels and a 0..100 signal for one masked message, or null when the model declines
     * or is unavailable (the caller then sends the message, to fail safe). Suspends: the model
     * runs off the main thread and loads on first use. */
    suspend fun label(sender: String, maskedText: String): OnDeviceResult?
}

data class OnDeviceResult(val labels: List<String>, val signal: Int)

object NoOnDeviceAnalyzer : OnDeviceAnalyzer {
    override val installed = false

    override suspend fun label(sender: String, maskedText: String): OnDeviceResult? = null
}
