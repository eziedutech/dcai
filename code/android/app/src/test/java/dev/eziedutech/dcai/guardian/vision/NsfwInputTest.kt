package dev.eziedutech.dcai.guardian.vision

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class NsfwInputTest {
    private val n = NsfwInput.SIZE * NsfwInput.SIZE

    @Test
    fun pixelsAreNormalizedChannelPlanes() {
        val argb = IntArray(n) { 0xFF000000.toInt() }
        argb[0] = 0xFFFF8000.toInt() // r 255, g 128, b 0
        val x = NsfwInput.pixels(argb)
        assertEquals(3 * n, x.size)
        assertEquals(1f, x[0], 1e-6f)
        assertEquals((128 / 255f - 0.5f) / 0.5f, x[n], 1e-6f)
        assertEquals(-1f, x[2 * n], 1e-6f)
        assertEquals(-1f, x[1], 1e-6f)
    }

    @Test(expected = IllegalArgumentException::class)
    fun pixelsRejectWrongSize() {
        NsfwInput.pixels(IntArray(10))
    }

    @Test
    fun scoreIsTheNsfwProbabilityAsSeksual() {
        val s = NsfwInput.toScore(floatArrayOf(0.12f, 0.88f))!!
        assertEquals(Category.SEKSUAL, s.category)
        assertEquals(88, s.score)
        assertEquals(NsfwInput.VERSION, s.modelVersion)
    }

    @Test
    fun ordinaryOrBrokenOutputGivesNoScore() {
        assertNull(NsfwInput.toScore(floatArrayOf(0.999f, 0.001f)))
        assertNull(NsfwInput.toScore(floatArrayOf(1f)))
        assertNull(NsfwInput.toScore(floatArrayOf(0f, Float.NaN)))
    }

    @Test
    fun highScoreBlursTheWholeImage() {
        val d = ImagePolicy.decide(Trigger.PERCAKAPAN, Findings(sensitive = NsfwInput.toScore(floatArrayOf(0.1f, 0.9f))))
        assertEquals(Category.SEKSUAL, d.category)
        assertEquals(true, d.blurAll)
    }

    @Test
    fun atomicsMustBeOnEveryCore() {
        val a53 = "processor\t: 0\nFeatures\t: fp asimd evtstrm aes pmull sha1 sha2 crc32 cpuid\n"
        val a55 = "Features\t: fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp cpuid\n"
        assertEquals(false, CpuFeatures.atomicsIn(a53))
        assertEquals(true, CpuFeatures.atomicsIn(a55 + a55))
        assertEquals(false, CpuFeatures.atomicsIn(a55 + a53))
        assertEquals(false, CpuFeatures.atomicsIn(""))
    }
}
