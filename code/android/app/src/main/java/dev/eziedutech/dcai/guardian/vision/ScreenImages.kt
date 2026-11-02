package dev.eziedutech.dcai.guardian.vision

/** An on-screen rectangle in screen pixels (left, top inclusive; right, bottom exclusive). */
data class ScreenBox(val left: Int, val top: Int, val right: Int, val bottom: Int) {
    val width get() = right - left
    val height get() = bottom - top
    val area get() = width.toLong() * height

    fun contains(o: ScreenBox) = left <= o.left && top <= o.top && right >= o.right && bottom >= o.bottom
}

/**
 * Which pictures on a chat screen to judge. The classifier sees a 224 px square, so a whole
 * screenshot shrinks a chat photo to a few dozen pixels among bubbles and text; each picture
 * is cut out and judged on its own instead. Avatars, stickers and icons are too small to keep.
 */
object ScreenImages {
    /** At most this many pictures per screenshot (about 3.5 s each on a Cortex-A53). */
    const val MAX = 3

    /** A picture must be at least this share of the screen width on both sides. */
    private const val MIN_SHARE = 0.25

    fun pick(images: List<ScreenBox>, screenWidth: Int, screenHeight: Int): List<ScreenBox> {
        val min = (screenWidth * MIN_SHARE).toInt()
        val clipped = images.mapNotNull { b ->
            val c = ScreenBox(
                b.left.coerceAtLeast(0),
                b.top.coerceAtLeast(0),
                b.right.coerceAtMost(screenWidth),
                b.bottom.coerceAtMost(screenHeight),
            )
            c.takeIf { it.width >= min && it.height >= min }
        }.distinct().sortedByDescending { it.area }
        // A picture inside a larger kept one (a thumbnail inside its frame) adds nothing.
        val kept = ArrayList<ScreenBox>()
        for (b in clipped) if (kept.none { it.contains(b) }) kept.add(b)
        return kept.take(MAX)
    }
}
