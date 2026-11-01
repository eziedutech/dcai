package dev.eziedutech.dcai.guardian.ingest

import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import org.pytorch.executorch.extension.llm.LlmCallback
import org.pytorch.executorch.extension.llm.LlmGenerationConfig
import org.pytorch.executorch.extension.llm.LlmModule

/**
 * Hosts the ExecuTorch model in a separate process (":ondevice", see the manifest). Loading a
 * ~1 to 2 GB model is what pushes a small phone over its memory limit; keeping it here means a
 * Low Memory Killer kill lands on THIS process only. The dcAI UI, the accessibility service and
 * the live stream stay alive in the main process, and MessageIngest falls back to the online
 * path (fail safe) when a call here fails.
 *
 * The runtime loads lazily on first use and is evicted after a short idle so the model does not
 * sit in memory. No message text, prompt or output is ever logged.
 */
class OnDeviceModelService : Service() {
    private val scope = CoroutineScope(Dispatchers.Default + SupervisorJob())
    private val mutex = Mutex()
    private var module: LlmModule? = null
    private var evictJob: Job? = null

    private val binder = object : IOnDeviceModel.Stub() {
        override fun generate(prompt: String, callback: IOnDeviceCallback) {
            scope.launch {
                try {
                    val out = runGenerate(prompt)
                    callback.onResult(out)
                } catch (t: Throwable) {
                    Log.w(TAG, "ondevice generate failed: ${t.javaClass.simpleName}")
                    runCatching { callback.onError(t.javaClass.simpleName) }
                }
            }
        }
    }

    override fun onBind(intent: Intent?): IBinder = binder

    private suspend fun runGenerate(prompt: String): String = mutex.withLock {
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
        LlmModule(
            OnDeviceFiles.pte(this).absolutePath,
            OnDeviceFiles.tok(this).absolutePath,
            0f,
        ).apply { load() }

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

    override fun onDestroy() {
        scope.cancel()
        module?.close()
        module = null
        super.onDestroy()
    }

    private companion object {
        const val TAG = "dcai.ondevice"
        // The short student was exported at max_seq_len 512; the coded answer is a few tokens.
        const val MAX_SEQ_LEN = 512
        const val MAX_NEW_TOKENS = 8
        const val IDLE_EVICT_MS = 60_000L
    }
}
