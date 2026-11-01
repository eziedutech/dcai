package dev.eziedutech.dcai.guardian.ingest

import android.content.Context
import android.util.Log
import dev.eziedutech.dcai.guardian.net.BackendClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.security.MessageDigest

/**
 * The on-device stage 1 model files on this phone and their download. The parent downloads the
 * model (about 1 to 2 GB) only when they pick the on-device analysis mode; nothing ships in the
 * APK. The runtime that loads and runs the model lives in a separate process
 * ([OnDeviceModelService]); this class only manages the files, which both processes share.
 *
 * No message text is ever logged (only sizes and status).
 */
class OnDeviceModel(context: Context) {
    private val appContext = context.applicationContext
    private val dir = OnDeviceFiles.dir(appContext)
    private val pteFile = OnDeviceFiles.pte(appContext)
    private val tokFile = OnDeviceFiles.tok(appContext)
    private val okFile = OnDeviceFiles.ok(appContext)

    val installed: Boolean
        get() = OnDeviceFiles.installed(appContext)

    private fun installedVersion(): String? =
        runCatching { okFile.readText().trim() }.getOrNull()?.takeIf { it.isNotEmpty() }

    sealed interface Progress {
        data class Downloading(val done: Long, val total: Long) : Progress
        data object Verifying : Progress
        data object Done : Progress
        data class Failed(val reason: String) : Progress
    }

    /**
     * Make sure the model is present and verified, downloading it if needed (resumable). Reports
     * coarse progress. Returns true when the model is ready. The reason in a Failed step is a
     * short status, never message text.
     */
    suspend fun ensureDownloaded(client: BackendClient, onProgress: (Progress) -> Unit): Boolean =
        withContext(Dispatchers.IO) {
            try {
                dir.mkdirs()
                val manifest = client.stage1Manifest()
                if (installed && installedVersion() == manifest.version) {
                    onProgress(Progress.Done)
                    return@withContext true
                }
                fetchAndVerify(
                    client, "/v1/device/model/stage1-tokenizer.json", tokFile,
                    manifest.tokenizerBytes, manifest.tokenizerSha256, onProgress,
                )
                fetchAndVerify(
                    client, "/v1/device/model/stage1.pte", pteFile,
                    manifest.pteBytes, manifest.pteSha256, onProgress,
                )
                okFile.writeText(manifest.version)
                onProgress(Progress.Done)
                true
            } catch (t: Throwable) {
                Log.w(TAG, "ondevice model download failed: ${t.javaClass.simpleName}")
                onProgress(Progress.Failed(t.javaClass.simpleName))
                false
            }
        }

    private suspend fun fetchAndVerify(
        client: BackendClient,
        path: String,
        target: File,
        totalBytes: Long,
        expectedSha: String,
        onProgress: (Progress) -> Unit,
    ) {
        if (target.isFile && target.length() == totalBytes && sha256(target) == expectedSha) return
        val part = File(target.parentFile, target.name + ".part")
        client.downloadModelFile(path, part, totalBytes) { done, total ->
            onProgress(Progress.Downloading(done, total))
        }
        onProgress(Progress.Verifying)
        val actual = sha256(part)
        if (actual != expectedSha) {
            part.delete()
            throw IllegalStateException("sha256 mismatch")
        }
        target.delete()
        if (!part.renameTo(target)) throw IllegalStateException("rename failed")
    }

    /** Delete the downloaded model (parent switched back to online, or to free space). The
     * :ondevice process, if running, releases it on its own idle eviction or when it next fails
     * to load. */
    fun remove() {
        okFile.delete()
        pteFile.delete()
        tokFile.delete()
    }

    private fun sha256(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { input ->
            val buf = ByteArray(1 shl 16)
            while (true) {
                val n = input.read(buf)
                if (n < 0) break
                digest.update(buf, 0, n)
            }
        }
        return digest.digest().joinToString("") { "%02x".format(it) }
    }

    private companion object {
        const val TAG = "dcai.ondevice"
    }
}
