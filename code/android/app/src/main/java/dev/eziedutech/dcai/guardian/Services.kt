package dev.eziedutech.dcai.guardian

import android.content.Context
import dev.eziedutech.dcai.guardian.data.GuardianStore
import dev.eziedutech.dcai.guardian.ingest.DeviceCapabilities
import dev.eziedutech.dcai.guardian.ingest.ExecuTorchStage1Analyzer
import dev.eziedutech.dcai.guardian.ingest.MessageIngest
import dev.eziedutech.dcai.guardian.ingest.OnDeviceAnalyzer
import dev.eziedutech.dcai.guardian.ingest.OnDeviceModel
import dev.eziedutech.dcai.guardian.ingest.OnDeviceModelClient
import dev.eziedutech.dcai.guardian.net.BackendClient
import dev.eziedutech.dcai.guardian.vision.ImageGuard
import dev.eziedutech.dcai.guardian.vision.OnDeviceDetectors
import dev.eziedutech.dcai.guardian.vision.SensitiveModel
import dev.eziedutech.dcai.guardian.vision.VisionNsfwModel

/**
 * Small hand-wired container. The store is the source of truth for the server URL and the
 * token, so the client and the ingest are rebuilt whenever pairing changes.
 */
object ServiceLocator {
    @Volatile private var cached: Triple<String, BackendClient, MessageIngest>? = null

    fun store(context: Context): GuardianStore = GuardianStore(context.applicationContext)

    /** Backend client for the current server and token, or null when not paired. */
    fun client(context: Context): BackendClient? {
        val store = store(context)
        val server = store.serverUrl ?: return null
        val existing = cached
        if (existing != null && existing.first == server) return existing.second
        val client = BackendClient(server) { store(context).deviceToken }
        cached = Triple(
            server,
            client,
            MessageIngest(
                store, client, onDeviceAnalyzer(context),
                onDeviceAllowed = DeviceCapabilities.supportsOnDevice(context),
            ),
        )
        return client
    }

    fun ingest(context: Context): MessageIngest? {
        client(context) ?: return null
        return cached?.third
    }

    @Volatile private var sensitive: SensitiveModel? = null

    /** The bundled sexual-content classifier (Falconsai ViT, Apache-2.0). Without its asset,
     * [SensitiveModel.installed] is false and only faces and personal text are detected. */
    fun sensitiveModel(context: Context): SensitiveModel =
        sensitive ?: VisionNsfwModel(context).also { sensitive = it }

    @Volatile private var model: OnDeviceModel? = null
    @Volatile private var analyzer: OnDeviceAnalyzer? = null

    /** The on-device stage 1 model (the Llama .pte mode): its files, download and runtime.
     * Nothing is downloaded until the parent picks on-device mode, so [OnDeviceModel.installed]
     * stays false and ingest keeps to the online path by default. */
    fun onDeviceModel(context: Context): OnDeviceModel =
        model ?: OnDeviceModel(context.applicationContext).also { model = it }

    /** The analyzer that drives message labelling on the phone. It runs the model in the
     * separate :ondevice process through an [OnDeviceModelClient]; the downloaded files are
     * shared with [onDeviceModel]. */
    fun onDeviceAnalyzer(context: Context): OnDeviceAnalyzer =
        analyzer ?: ExecuTorchStage1Analyzer(
            context.applicationContext,
            OnDeviceModelClient(context),
        ).also { analyzer = it }

    @Volatile private var detectors: OnDeviceDetectors? = null

    private fun detectors(context: Context): OnDeviceDetectors =
        detectors ?: OnDeviceDetectors(sensitiveModel(context)).also { detectors = it }

    fun imageGuard(context: Context): ImageGuard? {
        val client = client(context) ?: return null
        val ingest = cached?.third ?: return null
        return ImageGuard(store(context), client, ingest, detectors(context))
    }

    fun reset() {
        cached = null
    }
}
