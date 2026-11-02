package dev.eziedutech.dcai.guardian.vision

import android.content.Context
import android.graphics.Bitmap
import android.media.MediaMetadataRetriever
import android.net.Uri

/**
 * Frames taken from a video on the phone, in memory. The video is read from the content URI
 * the chat app granted and never stored or sent.
 */
object VideoFrames {
    /** Longest side of a frame; both models scale down from here. */
    const val MAX_SIDE = 480

    /**
     * `count` frames spread evenly over the clip, at `count` equal slices' midpoints, so a
     * frame is never the black first or last instant. code/vision/train_violence.py samples
     * the same way.
     */
    fun extract(context: Context, uri: Uri, count: Int): List<Bitmap> {
        val retriever = MediaMetadataRetriever()
        try {
            retriever.setDataSource(context, uri)
            val durationMs = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toLongOrNull() ?: 0L
            return VideoPolicy.timesUs(durationMs, count).mapNotNull { t ->
                retriever.getScaledFrameAtTime(t, MediaMetadataRetriever.OPTION_CLOSEST, MAX_SIDE, MAX_SIDE)
            }
        } finally {
            retriever.release()
        }
    }
}
