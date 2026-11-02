package dev.eziedutech.dcai.guardian.vision

import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Test

class RecentImagesTest {
    @After fun reset() = RecentImages.clear()

    @Test
    fun aPictureStillOnScreenIsReportedOnce() {
        assertEquals(true, RecentImages.firstTime("t", 0x0F0F0F0F0F0F0F0FL, 0))
        assertEquals(false, RecentImages.firstTime("t", 0x0F0F0F0F0F0F0F0FL, 15_000))
        // A slightly different crop of the same picture (2 bits off) is still the same.
        assertEquals(false, RecentImages.firstTime("t", 0x0F0F0F0F0F0F0F0CL, 30_000))
    }

    @Test
    fun anotherChatOrAnotherPictureOrADayLaterCountsAgain() {
        RecentImages.firstTime("t", 0x0F0F0F0F0F0F0F0FL, 0)
        assertEquals(true, RecentImages.firstTime("u", 0x0F0F0F0F0F0F0F0FL, 1))
        assertEquals(true, RecentImages.firstTime("t", 0x7FF0F0F0F0F0F0F0L, 2))
        assertEquals(true, RecentImages.firstTime("t", 0x0F0F0F0F0F0F0F0FL, RecentImages.WINDOW_MS + 1))
    }

    @Test
    fun aPictureWhoseReportFailedIsTriedAgain() {
        assertEquals(true, RecentImages.firstTime("t", 0x0F0F0F0F0F0F0F0FL, 0))
        RecentImages.forget("t", 0x0F0F0F0F0F0F0F0FL)
        assertEquals(true, RecentImages.firstTime("t", 0x0F0F0F0F0F0F0F0FL, 1))
        assertEquals(false, RecentImages.firstTime("t", 0x0F0F0F0F0F0F0F0FL, 2))
    }
}
