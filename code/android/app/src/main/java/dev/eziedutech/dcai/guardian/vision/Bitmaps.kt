package dev.eziedutech.dcai.guardian.vision

import android.content.ContentResolver
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.net.Uri

/** Image helpers. Everything stays in memory; nothing here writes an image anywhere. */
object Bitmaps {
    /** Longest side used for detection; enough for faces and printed text. */
    private const val MAX_SIDE = 1280

    fun decode(resolver: ContentResolver, uri: Uri): Bitmap? {
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        // With inJustDecodeBounds the call returns null and fills bounds.
        val stream = resolver.openInputStream(uri) ?: return null
        stream.use { BitmapFactory.decodeStream(it, null, bounds) }
        if (bounds.outWidth <= 0 || bounds.outHeight <= 0) return null
        var sample = 1
        while (maxOf(bounds.outWidth, bounds.outHeight) / (sample * 2) >= MAX_SIDE) sample *= 2
        val options = BitmapFactory.Options().apply { inSampleSize = sample }
        return resolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, options) }
    }

    fun dHash(bitmap: Bitmap): Long {
        val small = Bitmap.createScaledBitmap(bitmap, ImageHash.WIDTH, ImageHash.HEIGHT, true)
        val pixels = IntArray(ImageHash.WIDTH * ImageHash.HEIGHT)
        small.getPixels(pixels, 0, ImageHash.WIDTH, 0, 0, ImageHash.WIDTH, ImageHash.HEIGHT)
        if (small !== bitmap) small.recycle()
        val gray = IntArray(pixels.size) { i ->
            val p = pixels[i]
            (Color.red(p) * 299 + Color.green(p) * 587 + Color.blue(p) * 114) / 1000
        }
        return ImageHash.dHash(gray)
    }
}
