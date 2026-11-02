package dev.eziedutech.dcai.guardian.vision

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class VideoPolicyTest {
    @Test
    fun timesAreSliceMidpointsInMicroseconds() {
        assertEquals(listOf(1_250_000L, 3_750_000L, 6_250_000L, 8_750_000L), VideoPolicy.timesUs(10_000, 4))
        // Never the first or last instant, where a clip is often black.
        val t = VideoPolicy.timesUs(3_000, 16)
        assertTrue(t.first() > 0 && t.last() < 3_000_000L)
        assertEquals(16, t.size)
    }

    @Test
    fun aClipWithoutDurationGivesOneFrameAtTheStart() {
        assertEquals(listOf(0L), VideoPolicy.timesUs(0, 4))
        assertEquals(emptyList<Long>(), VideoPolicy.timesUs(5_000, 0))
    }

    @Test
    fun spreadPicksEvenlyAndKeepsShortListsWhole() {
        assertEquals(listOf(2, 6, 10, 14), VideoPolicy.spread(16, 4))
        assertEquals(listOf(0, 1, 2), VideoPolicy.spread(3, 4))
        assertEquals(emptyList<Int>(), VideoPolicy.spread(0, 4))
    }

    @Test
    fun overUsesTheCategoryThreshold() {
        val s = SensitiveScore(Category.SEKSUAL, 72, "m")
        assertTrue(VideoPolicy.over(s, emptyMap()))
        assertFalse(VideoPolicy.over(s, mapOf(Category.SEKSUAL to 74)))
        assertFalse(VideoPolicy.over(null, emptyMap()))
    }

    @Test
    fun topIsTheScoreFurthestAboveItsThreshold() {
        val sexual = SensitiveScore(Category.SEKSUAL, 75, "img")
        val violent = SensitiveScore(Category.KEKERASAN, 78, "vid")
        // Violence's threshold was raised after a confirmed false detection: 78 - 80 < 75 - 70.
        val raised = mapOf(Category.KEKERASAN to 80)
        assertEquals(sexual, VideoPolicy.top(listOf(null, sexual, violent), raised))
        assertEquals(violent, VideoPolicy.top(listOf(sexual, violent)))
        assertNull(VideoPolicy.top(listOf(null, null)))
    }

    @Test
    fun aSensitiveClipIsBlurredWholeLikeAnImage() {
        val top = VideoPolicy.top(listOf(SensitiveScore(Category.KEKERASAN, 90, "vid")))
        val d = ImagePolicy.decide(Trigger.PERCAKAPAN, Findings(sensitive = top))
        assertEquals(Category.KEKERASAN, d.category)
        assertEquals(Action.DIKABURKAN, d.action)
        assertTrue(d.blurAll)
    }
}
