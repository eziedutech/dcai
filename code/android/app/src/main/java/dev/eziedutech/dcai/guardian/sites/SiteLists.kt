package dev.eziedutech.dcai.guardian.sites

import android.content.Context
import android.util.Log
import dev.eziedutech.dcai.guardian.net.BackendClient
import dev.eziedutech.dcai.guardian.net.SiteManifest
import kotlinx.serialization.json.Json
import java.io.File
import java.io.RandomAccessFile
import java.nio.channels.FileChannel
import java.security.MessageDigest

/**
 * The category lists on the phone: downloaded from the backend, checked against the
 * manifest's SHA-256, memory-mapped for lookups. A list that fails the check is not used.
 */
class SiteLists(context: Context, private val client: BackendClient) {
    private val dir = File(context.filesDir, "sites").apply { mkdirs() }
    private val manifestFile = File(dir, "manifest.json")
    private val json = Json { ignoreUnknownKeys = true }

    /** The manifest on the phone, or null before the first download. */
    fun manifest(): SiteManifest? =
        runCatching { json.decodeFromString<SiteManifest>(manifestFile.readText()) }.getOrNull()

    /** Downloads what changed. Keeps the lists already on the phone if the backend is down. */
    suspend fun sync(): SiteManifest? {
        val remote = runCatching { client.siteManifest() }
            .onFailure { Log.d(TAG, "site manifest failed: ${it.javaClass.simpleName}") }
            .getOrNull() ?: return manifest()
        for (entry in remote.categories) {
            val file = File(dir, "${entry.name}.bin")
            if (file.exists() && sha256(file) == entry.sha256) continue
            val part = File(dir, "${entry.name}.part")
            // One retry: a large list can be cut off when the network changes underneath.
            val ok = (1..2).any { attempt ->
                val got = runCatching { client.downloadSiteList(entry.name, part) }
                    .onFailure { Log.d(TAG, "site list ${entry.name} attempt $attempt failed: ${it.javaClass.simpleName}") }
                    .isSuccess
                got && part.exists() && sha256(part) == entry.sha256
            }
            if (ok) part.renameTo(file.also { it.delete() }) else part.delete()
        }
        manifestFile.writeText(json.encodeToString(remote))
        return remote
    }

    /** Lists on the phone that match the manifest, ready for lookups. */
    fun load(): List<SiteList> {
        val manifest = manifest() ?: return emptyList()
        return manifest.categories.mapNotNull { entry ->
            val file = File(dir, "${entry.name}.bin")
            if (!file.exists() || file.length() != entry.bytes) return@mapNotNull null
            runCatching {
                RandomAccessFile(file, "r").use { raf ->
                    SiteList(entry.name, raf.channel.map(FileChannel.MapMode.READ_ONLY, 0, raf.length()))
                }
            }.onFailure { Log.d(TAG, "site list unreadable: ${entry.name}") }.getOrNull()
        }
    }

    fun clear() {
        dir.listFiles()?.forEach { it.delete() }
    }

    private fun sha256(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { input ->
            val buffer = ByteArray(1 shl 16)
            while (true) {
                val n = input.read(buffer)
                if (n < 0) break
                digest.update(buffer, 0, n)
            }
        }
        return digest.digest().joinToString("") { "%02x".format(it) }
    }

    private companion object {
        const val TAG = "dcai.sites"
    }
}
