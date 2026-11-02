package dev.eziedutech.dcai.guardian.vision

import android.content.Context
import android.graphics.Bitmap
import android.os.SystemClock
import android.util.Log
import dev.eziedutech.dcai.guardian.BuildConfig
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.tensorflow.lite.Interpreter
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.channels.FileChannel
import kotlin.math.roundToInt

/**
 * The sexual-content classifier: Falconsai/nsfw_image_detection (ViT, Apache-2.0), used as
 * published and exported by code/vision/export_nsfw.py to a LiteRT .tflite bundled in the APK
 * assets. It runs on the phone; the image never leaves it. Its accuracy is the figure its
 * source states; dcAI has not measured it.
 *
 * Violence (KEKERASAN) is a video model in a later build; this one only scores SEKSUAL.
 *
 * The model is memory-mapped from the APK on first use and released after a short idle, so
 * the ~90 MB model does not sit in the main process between images. Call [score] off the main
 * thread.
 */
class VisionNsfwModel(context: Context) : SensitiveModel {
    private val app = context.applicationContext
    private val lock = Any()
    private val scope = CoroutineScope(Dispatchers.Default + SupervisorJob())
    private var interpreter: Interpreter? = null
    private var evictJob: Job? = null

    override val installed: Boolean =
        runCatching { app.assets.list(ASSET_DIR)?.contains(MODEL) == true }.getOrDefault(false)

    override fun score(bitmap: Bitmap): SensitiveScore? {
        if (!installed) return null
        return try {
            val input = NsfwInput.buffer(NsfwInput.pixels(scaled(bitmap)))
            val probs = Array(1) { FloatArray(2) }
            val started = SystemClock.elapsedRealtime()
            synchronized(lock) {
                val m = interpreter ?: load().also { interpreter = it }
                m.run(input, probs)
            }
            val ms = SystemClock.elapsedRealtime() - started
            val result = NsfwInput.toScore(probs[0])
            // Timing only in release. Debug builds add the score (a number, nothing about the
            // image) to calibrate the threshold on the test phone.
            if (BuildConfig.DEBUG) {
                Log.i(TAG, "nsfw scored in $ms ms score=${result?.score ?: 0}")
            } else {
                Log.i(TAG, "nsfw scored in $ms ms")
            }
            scheduleEvict()
            result
        } catch (t: Throwable) {
            // Type only. A failed model leaves the image to the face and text detectors.
            Log.w(TAG, "nsfw score failed: ${t.javaClass.simpleName}")
            null
        }
    }

    private fun scaled(bitmap: Bitmap): IntArray {
        val small = Bitmap.createScaledBitmap(bitmap, NsfwInput.SIZE, NsfwInput.SIZE, true)
        val px = IntArray(NsfwInput.SIZE * NsfwInput.SIZE)
        small.getPixels(px, 0, NsfwInput.SIZE, 0, 0, NsfwInput.SIZE, NsfwInput.SIZE)
        if (small !== bitmap) small.recycle()
        return px
    }

    /** Maps the uncompressed asset (build.gradle.kts noCompress) straight from the APK. */
    private fun load(): Interpreter {
        val mapped = app.assets.openFd("$ASSET_DIR/$MODEL").use { fd ->
            FileInputStream(fd.fileDescriptor).channel.use {
                it.map(FileChannel.MapMode.READ_ONLY, fd.startOffset, fd.declaredLength)
            }
        }
        return Interpreter(mapped, Interpreter.Options().setNumThreads(THREADS))
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
        const val TAG = "dcai.vision"
        const val ASSET_DIR = "vision"
        const val MODEL = "nsfw.tflite"
        // 4 threads measured no faster than 2 on a Helio P35 (about 3.5 s warm, 5.5 s cold).
        const val THREADS = 2
        const val IDLE_EVICT_MS = 60_000L
    }
}

/**
 * The classifier's input and output as pure functions, unit tested without the runtime.
 * Must match code/vision/export_nsfw.py (phone_preprocess and the label order).
 */
object NsfwInput {
    const val SIZE = 224
    const val VERSION = "falconsai-nsfw-image-detection+litert-int8"

    // ViTImageProcessor for this model: mean 0.5, std 0.5 on every channel (nsfw.json).
    private const val MEAN = 0.5f
    private const val STD = 0.5f

    /** ARGB pixels (SIZE x SIZE, row-major) to normalized CHW floats. */
    fun pixels(argb: IntArray): FloatArray {
        require(argb.size == SIZE * SIZE) { "expected ${SIZE * SIZE} pixels" }
        val plane = SIZE * SIZE
        val out = FloatArray(3 * plane)
        for (i in 0 until plane) {
            val p = argb[i]
            out[i] = (((p shr 16) and 0xFF) / 255f - MEAN) / STD
            out[plane + i] = (((p shr 8) and 0xFF) / 255f - MEAN) / STD
            out[2 * plane + i] = ((p and 0xFF) / 255f - MEAN) / STD
        }
        return out
    }

    /** The model's float input as a native-order direct buffer. */
    fun buffer(chw: FloatArray): ByteBuffer {
        val b = ByteBuffer.allocateDirect(chw.size * 4).order(ByteOrder.nativeOrder())
        b.asFloatBuffer().put(chw)
        return b
    }

    /** Softmax output [normal, nsfw] to a SEKSUAL score 0..100; null when it rounds to 0. */
    fun toScore(probs: FloatArray): SensitiveScore? {
        if (probs.size < 2 || probs[1].isNaN()) return null
        val score = (probs[1] * 100f).roundToInt().coerceIn(0, 100)
        return if (score == 0) null else SensitiveScore(Category.SEKSUAL, score, VERSION)
    }
}
