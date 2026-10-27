package dev.eziedutech.dcai.guardian

import android.content.Context
import dev.eziedutech.dcai.guardian.data.GuardianStore
import dev.eziedutech.dcai.guardian.ingest.MessageIngest
import dev.eziedutech.dcai.guardian.net.BackendClient

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

    fun reset() {
        cached = null
    }
}
