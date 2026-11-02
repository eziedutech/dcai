package dev.eziedutech.dcai.guardian.vision

import android.content.Context
import android.graphics.Bitmap
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.pytorch.executorch.EValue
import org.pytorch.executorch.Module
import org.pytorch.executorch.Tensor
import java.io.File
import kotlin.math.roundToInt

/**
 * The sexual-content classifier: Falconsai/nsfw_image_detection (ViT, Apache-2.0), used as
 * published and exported by code/vision/export_nsfw.py to an ExecuTorch .pte bundled in the
 * APK assets. It runs on the phone on the same runtime as the message model; the image never
 * leaves it. Its accuracy is the figure its source states; dcAI has not measured it.
 *
 * Violence (KEKERASAN) is a video model in a later build; this one only scores SEKSUAL.
 *
 * The runtime loads on first use and is released after a short idle, so the ~90 MB model does
 * not sit in the main process between images. Call [score] off the main thread.
 */
class VisionNsfwModel(context: Context) : SensitiveModel {
    private val app = context.applicationContext
    private val lock = Any()
    private val scope = CoroutineScope(Dispatchers.Default + SupervisorJob())
    private var module: Module? = null
    private var evictJob: Job? = null

    // The executorch-android runtime is built with ARMv8.1 LSE atomics inline, so its generic
    // Module path dies with SIGILL on ARMv8.0 cores (Cortex-A53, seen on the test phone). On
    // such a phone the model stays off and images get the face and text detectors only.
    override val installed: Boolean =
        CpuFeatures.hasAtomics() &&
            runCatching { app.assets.list(ASSET_DIR)?.contains(PTE) == true }.getOrDefault(false)

    override fun score(bitmap: Bitmap): SensitiveScore? {
        if (!installed) return null
        return try {
            val input = NsfwInput.pixels(scaled(bitmap))
            val probs = synchronized(lock) {
                val m = module ?: load().also { module = it }
                m.forward(EValue.from(Tensor.fromBlob(input, longArrayOf(1, 3, NsfwInput.SIZE.toLong(), NsfwInput.SIZE.toLong()))))[0]
                    .toTensor().dataAsFloatArray
            }
            scheduleEvict()
            NsfwInput.toScore(probs)
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

    /** The runtime needs a file path, so the asset is copied once to no-backup storage. */
    private fun load(): Module {
        val file = File(app.noBackupFilesDir, "vision/$PTE")
        val size = app.assets.openFd("$ASSET_DIR/$PTE").use { it.length }
        if (!file.exists() || file.length() != size) {
            file.parentFile?.mkdirs()
            val tmp = File(file.path + ".part")
            app.assets.open("$ASSET_DIR/$PTE").use { src -> tmp.outputStream().use { src.copyTo(it) } }
            if (!tmp.renameTo(file)) error("rename failed")
        }
        return Module.load(file.absolutePath, Module.LOAD_MODE_MMAP)
    }

    private fun scheduleEvict() {
        evictJob?.cancel()
        evictJob = scope.launch {
            delay(IDLE_EVICT_MS)
            synchronized(lock) {
                module?.destroy()
                module = null
            }
        }
    }

    private companion object {
        const val TAG = "dcai.vision"
        const val ASSET_DIR = "vision"
        // Stored uncompressed (build.gradle.kts noCompress) so openFd can read its length.
        const val PTE = "nsfw.pte"
        const val IDLE_EVICT_MS = 60_000L
    }
}

/** CPU features read from /proc/cpuinfo ("Features" lines, the kernel's hwcaps). */
object CpuFeatures {
    fun hasAtomics(): Boolean =
        runCatching { atomicsIn(File("/proc/cpuinfo").readText()) }.getOrDefault(false)

    /** True when every core lists "atomics" (a big.LITTLE mix must not schedule onto a core
     * without them). */
    fun atomicsIn(cpuinfo: String): Boolean {
        val lines = cpuinfo.lineSequence().filter { it.startsWith("Features") }.toList()
        return lines.isNotEmpty() && lines.all { "atomics" in it.substringAfter(':').trim().split(' ') }
    }
}

/**
 * The classifier's input and output as pure functions, unit tested without the runtime.
 * Must match code/vision/export_nsfw.py (phone_preprocess and the label order).
 */
object NsfwInput {
    const val SIZE = 224
    const val VERSION = "falconsai-nsfw-image-detection+xnnpack-int8"

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

    /** Softmax output [normal, nsfw] to a SEKSUAL score 0..100; null when it rounds to 0. */
    fun toScore(probs: FloatArray): SensitiveScore? {
        if (probs.size < 2 || probs[1].isNaN()) return null
        val score = (probs[1] * 100f).roundToInt().coerceIn(0, 100)
        return if (score == 0) null else SensitiveScore(Category.SEKSUAL, score, VERSION)
    }
}
