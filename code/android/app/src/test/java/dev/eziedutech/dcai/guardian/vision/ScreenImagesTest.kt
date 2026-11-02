package dev.eziedutech.dcai.guardian.vision

import org.junit.Assert.assertEquals
import org.junit.Test

class ScreenImagesTest {
    private val w = 720
    private val h = 1600

    @Test
    fun keepsChatPhotosAndDropsAvatarsAndIcons() {
        val photo = ScreenBox(200, 400, 680, 900)
        val avatar = ScreenBox(10, 60, 90, 140)
        val icon = ScreenBox(600, 1500, 660, 1560)
        assertEquals(listOf(photo), ScreenImages.pick(listOf(avatar, photo, icon), w, h))
    }

    @Test
    fun clipsToTheScreenAndDropsWhatIsMostlyOffScreen() {
        val partly = ScreenBox(200, 1400, 680, 1900)
        val barely = ScreenBox(200, 1550, 680, 2000)
        assertEquals(listOf(ScreenBox(200, 1400, 680, 1600)), ScreenImages.pick(listOf(partly, barely), w, h))
    }

    @Test
    fun aThumbnailInsideItsFrameCountsOnce() {
        val frame = ScreenBox(180, 380, 700, 920)
        val inner = ScreenBox(200, 400, 680, 900)
        assertEquals(listOf(frame), ScreenImages.pick(listOf(inner, frame), w, h))
    }

    @Test
    fun largestFirstAndAtMostMax() {
        val boxes = (0 until 5).map { i -> ScreenBox(0, i * 300, 200 + i * 40, i * 300 + 250) }
        val picked = ScreenImages.pick(boxes, w, h)
        assertEquals(ScreenImages.MAX, picked.size)
        assertEquals(boxes[4], picked[0])
    }

    @Test
    fun aWallpaperIsNotAPicture() {
        val wallpaper = ScreenBox(0, 184, 720, 1440)
        val photo = ScreenBox(42, 563, 494, 1196)
        assertEquals(listOf(photo), ScreenImages.pick(listOf(wallpaper, photo), 720, 1440))
    }

    @Test
    fun picturesAreKnownByClassOrViewId() {
        assertEquals(true, ScreenImages.isPicture("android.widget.ImageView", null))
        assertEquals(true, ScreenImages.isPicture("android.widget.Button", "com.whatsapp:id/image"))
        assertEquals(true, ScreenImages.isPicture("android.widget.FrameLayout", "com.whatsapp:id/media_container"))
        assertEquals(false, ScreenImages.isPicture("android.widget.Button", "com.whatsapp:id/send"))
        assertEquals(false, ScreenImages.isPicture("android.widget.TextView", null))
    }

    @Test
    fun aVideoCoverIsKnownByItsDescriptionOrId() {
        assertEquals(true, ScreenImages.isVideo("com.whatsapp:id/thumb", "Video, HD, duration 39 seconds"))
        assertEquals(true, ScreenImages.isVideo("com.whatsapp:id/conversation_row_video", null))
        assertEquals(false, ScreenImages.isVideo("com.whatsapp:id/image", "Photo"))
        assertEquals(false, ScreenImages.isVideo("com.whatsapp:id/thumb", "Videography studio logo"))
        assertEquals(false, ScreenImages.isVideo(null, null))
    }

    @Test
    fun aVideoCoverInsideItsFrameMakesTheFrameAVideo() {
        // WhatsApp, measured: media_container holds the cover ImageView described as a video.
        val frame = ScreenBox(34, 621, 502, 1270)
        val cover = ScreenBox(42, 629, 494, 1262, video = true)
        assertEquals(listOf(frame.copy(video = true)), ScreenImages.pick(listOf(frame, cover), 720, 1440))
        assertEquals(listOf(frame), ScreenImages.pick(listOf(frame, cover.copy(video = false)), 720, 1440))
    }
}
