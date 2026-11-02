package dev.eziedutech.dcai.guardian.vision

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class ViolenceInputTest {
    private val plane = ViolenceInput.SIZE * ViolenceInput.SIZE

    @Test
    fun framesBecomeTimeMajorRgbInZeroToOne() {
        val frames = List(ViolenceInput.FRAMES) { t -> IntArray(plane) { if (t == 1) 0xFF336699.toInt() else 0xFF000000.toInt() } }
        val out = ViolenceInput.pixels(frames)
        assertEquals(ViolenceInput.FRAMES * plane * 3, out.size)
        // Frame 1, first pixel: channels last.
        val at = plane * 3
        assertEquals(0x33 / 255f, out[at], 1e-6f)
        assertEquals(0x66 / 255f, out[at + 1], 1e-6f)
        assertEquals(0x99 / 255f, out[at + 2], 1e-6f)
        assertEquals(0f, out[0], 0f)
    }

    @Test(expected = IllegalArgumentException::class)
    fun theFrameCountIsFixed() {
        ViolenceInput.pixels(List(ViolenceInput.FRAMES - 1) { IntArray(plane) })
    }

    @Test
    fun scoreIsTheViolenceProbability() {
        val s = ViolenceInput.toScore(floatArrayOf(0.2f, 0.8f))!!
        assertEquals(Category.KEKERASAN, s.category)
        assertEquals(80, s.score)
        assertNull(ViolenceInput.toScore(floatArrayOf(1f, 0f)))
    }
}
