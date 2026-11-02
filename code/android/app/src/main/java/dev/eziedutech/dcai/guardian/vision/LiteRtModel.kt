package dev.eziedutech.dcai.guardian.vision

import android.content.Context
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.tensorflow.lite.Interpreter
import java.io.FileInputStream
import java.nio.channels.FileChannel

/**
 * A LiteRT model bundled in the APK assets (uncompressed, build.gradle.kts noCompress). It
 * is memory-mapped on first use and released after a short idle, so a large model does not
 * sit in the main process between checks. Call [run] off the main thread.
 */
class LiteRtModel(context: Context, private val asset: String, private val threads: Int = 2) {
    private val app = context.applicationContext
    private val lock = Any()
    private val scope = CoroutineScope(Dispatchers.Default + SupervisorJob())
    private var interpreter: Interpreter? = null
    private var evictJob: Job? = null

    val installed: Boolean = runCatching {
        val dir = asset.substringBeforeLast('/', "")
        app.assets.list(dir)?.contains(asset.substringAfterLast('/')) == true
    }.getOrDefault(false)

    fun run(input: Any, output: Any) {
        synchronized(lock) {
            val m = interpreter ?: load().also { interpreter = it }
            m.run(input, output)
        }
        scheduleEvict()
    }

    private fun load(): Interpreter {
        val mapped = app.assets.openFd(asset).use { fd ->
            FileInputStream(fd.fileDescriptor).channel.use {
                it.map(FileChannel.MapMode.READ_ONLY, fd.startOffset, fd.declaredLength)
            }
        }
        return Interpreter(mapped, Interpreter.Options().setNumThreads(threads))
    }

    private fun scheduleEvict() {
        evictJob?.cancel()
        evictJob = scope.launch {
            delay(IDLE_EVICT_MS)
            synchronized(lock) {
                interpreter?.close()
                interpreter = null
            }
        }
    }

    private companion object {
        const val IDLE_EVICT_MS = 60_000L
    }
}
