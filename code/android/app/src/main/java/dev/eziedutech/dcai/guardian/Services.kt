package dev.eziedutech.dcai.guardian

import android.content.Context
import dev.eziedutech.dcai.guardian.data.GuardianStore
import dev.eziedutech.dcai.guardian.ingest.MessageIngest
import dev.eziedutech.dcai.guardian.net.BackendClient
import dev.eziedutech.dcai.guardian.vision.ImageGuard
import dev.eziedutech.dcai.guardian.vision.NoSensitiveModel
import dev.eziedutech.dcai.guardian.vision.OnDeviceDetectors
import dev.eziedutech.dcai.guardian.vision.SensitiveModel

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
        cached = Triple(server, client, MessageIngest(store, client))
        return client
    }

    fun ingest(context: Context): MessageIngest? {
        client(context) ?: return null
        return cached?.third
    }

    /** A licensed sensitive-image classifier is registered here; none ships with this build. */
    val sensitiveModel: SensitiveModel = NoSensitiveModel

    private val detectors by lazy { OnDeviceDetectors(sensitiveModel) }

    fun imageGuard(context: Context): ImageGuard? {
        val client = client(context) ?: return null
        val ingest = cached?.third ?: return null
        return ImageGuard(store(context), client, ingest, detectors)
    }

    fun reset() {
        cached = null
    }
}
