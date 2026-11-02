package dev.eziedutech.dcai.guardian.vision

import android.content.Context
import android.graphics.Bitmap
import android.os.SystemClock
import android.util.Log
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.roundToInt

/**
 * A model that judges a whole clip from its frames, in order. It runs on the phone; the
 * video never leaves it.
 */
interface VideoModel {
    val installed: Boolean

    /** How many frames, evenly spread over the clip, the model reads. */
    val frames: Int

    /** The clip's sensitive score, or null when nothing scores. */
    fun score(frames: List<Bitmap>): SensitiveScore?
}

/**
 * The violence classifier: MoViNet-A0 trained by code/vision/train_violence.py on the VID
 * dataset and exported to LiteRT. The asset ships only after training; until then
 * [installed] is false and videos are checked for sexual content alone. Its accuracy is the
 * test-split figure in the violence.json written by that script, and nothing else.
 */
class VisionViolenceModel(context: Context) : VideoModel {
    private val model = LiteRtModel(context, "vision/violence.tflite", threads = 2)

    override val installed: Boolean get() = model.installed
    override val frames: Int = ViolenceInput.FRAMES

    override fun score(frames: List<Bitmap>): SensitiveScore? {
        if (!installed || frames.size != ViolenceInput.FRAMES) return null
        return try {
            val input = ViolenceInput.buffer(ViolenceInput.pixels(frames.map(::scaled)))
            val probs = Array(1) { FloatArray(2) }
            val started = SystemClock.elapsedRealtime()
            model.run(input, probs)
            Log.i(TAG, "violence scored in ${SystemClock.elapsedRealtime() - started} ms")
            ViolenceInput.toScore(probs[0])
        } catch (t: Throwable) {
            Log.w(TAG, "violence score failed: ${t.javaClass.simpleName}")
            null
        }
    }

    private fun scaled(bitmap: Bitmap): IntArray {
        val size = ViolenceInput.SIZE
        val small = Bitmap.createScaledBitmap(bitmap, size, size, true)
        val px = IntArray(size * size)
        small.getPixels(px, 0, size, 0, 0, size, size)
        if (small !== bitmap) small.recycle()
        return px
    }

    private companion object {
        const val TAG = "dcai.vision"
    }
}

/**
 * The violence model's input and output as pure functions. Must match
 * code/vision/train_violence.py: [1, FRAMES, SIZE, SIZE, 3] RGB in 0..1, labels
 * ["normal", "kekerasan"].
 */
object ViolenceInput {
    const val FRAMES = 16
    const val SIZE = 172
    const val VERSION = "movinet-a0-vid+litert-int8"

    /** One ARGB array per frame (SIZE x SIZE, row-major) to NTHWC floats. */
    fun pixels(frames: List<IntArray>): FloatArray {
        require(frames.size == FRAMES) { "expected $FRAMES frames" }
        val plane = SIZE * SIZE
        val out = FloatArray(FRAMES * plane * 3)
        var o = 0
        for (frame in frames) {
            require(frame.size == plane) { "expected $plane pixels" }
            for (p in frame) {
                out[o++] = ((p shr 16) and 0xFF) / 255f
                out[o++] = ((p shr 8) and 0xFF) / 255f
                out[o++] = (p and 0xFF) / 255f
            }
        }
        return out
    }

    fun buffer(values: FloatArray): ByteBuffer {
        val b = ByteBuffer.allocateDirect(values.size * 4).order(ByteOrder.nativeOrder())
        b.asFloatBuffer().put(values)
        return b
    }

    /** Softmax output [normal, kekerasan] to a KEKERASAN score 0..100; null when it rounds to 0. */
    fun toScore(probs: FloatArray): SensitiveScore? {
        if (probs.size < 2 || probs[1].isNaN()) return null
        val score = (probs[1] * 100f).roundToInt().coerceIn(0, 100)
        return if (score == 0) null else SensitiveScore(Category.KEKERASAN, score, VERSION)
    }
}
