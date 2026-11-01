package dev.eziedutech.dcai.guardian.ingest

import android.content.Context
import android.util.Log
import dev.eziedutech.dcai.guardian.net.BackendClient
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import org.pytorch.executorch.extension.llm.LlmCallback
import org.pytorch.executorch.extension.llm.LlmGenerationConfig
import org.pytorch.executorch.extension.llm.LlmModule
import java.io.File
import java.security.MessageDigest

/**
 * The on-device stage 1 model on this phone: its files, its download, and the ExecuTorch
 * runtime over it. The parent downloads it (about 2 GB) only when they pick the on-device
 * analysis mode; nothing ships in the APK.
 *
 * The files live in noBackupFilesDir (sandboxed, never in a cloud backup). The runtime is
 * loaded lazily on first use and evicted after a short idle so a 2 GB model does not sit in
 * memory and invite the Low Memory Killer. All work is off the main thread.
 *
 * No message text, prompt or model output is ever logged (only sizes and status), so raw
 * conversation text never reaches a log.
 */
class OnDeviceModel(context: Context) {
    private val appContext = context.applicationContext
    private val dir = File(appContext.noBackupFilesDir, DIR)
    private val pteFile = File(dir, PTE)
    private val tokFile = File(dir, TOK)
    // Written only after both files verify against the manifest; holds the installed version.
    private val okFile = File(dir, OK)

    val installed: Boolean
        get() = pteFile.isFile && tokFile.isFile && okFile.isFile

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
                // Tokenizer first (small), then the large .pte; each to a .part, verified, renamed.
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

    /** Delete the downloaded model (parent switched back to online, or to free space). */
    fun remove() {
        close()
        okFile.delete()
        pteFile.delete()
        tokFile.delete()
    }

    // ------------------------------------------------------------------ runtime

    private val mutex = Mutex()
    private var module: LlmModule? = null
    private var evictJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.Default + SupervisorJob())

    /** Run one prompt to completion and return the generated text (prompt echo off). Loads the
     * runtime on first use and keeps it warm until idle. */
    suspend fun generate(prompt: String): String = mutex.withLock {
        val m = module ?: createModule().also { module = it }
        val out = StringBuilder()
        val config = LlmGenerationConfig.create()
            .seqLen(MAX_SEQ_LEN)
            .maxNewTokens(MAX_NEW_TOKENS)
            .echo(false)
            .temperature(0f)
            // The prompt already carries a literal <|begin_of_text|>, so the runtime adds none.
            .numBos(0)
            .numEos(0)
            .build()
        m.generate(prompt, config, object : LlmCallback {
            override fun onResult(result: String) {
                out.append(result)
            }
        })
        scheduleEvict()
        out.toString()
    }

    private fun createModule(): LlmModule =
        LlmModule(pteFile.absolutePath, tokFile.absolutePath, 0f).apply { load() }

    private fun scheduleEvict() {
        evictJob?.cancel()
        evictJob = scope.launch {
            delay(IDLE_EVICT_MS)
            mutex.withLock {
                module?.close()
                module = null
            }
        }
    }

    fun close() {
        evictJob?.cancel()
        module?.close()
        module = null
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
        const val DIR = "ondevice"
        const val PTE = "stage1.pte"
        const val TOK = "tokenizer.json"
        const val OK = "installed.json"
        // The model was exported at max_seq_len 1024; labels are short, so cap new tokens low.
        const val MAX_SEQ_LEN = 1024
        const val MAX_NEW_TOKENS = 64
        const val IDLE_EVICT_MS = 60_000L
    }
}
