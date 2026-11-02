package dev.eziedutech.dcai.guardian.vision

/** How a clip is judged from its frames. Pure Kotlin, unit tested without a phone. */
object VideoPolicy {
    /** Frames the (slow) image model reads per clip; it stops at the first sensitive one. */
    const val IMAGE_FRAMES = 4

    /** Midpoints of `count` equal slices of the clip, in microseconds. */
    fun timesUs(durationMs: Long, count: Int): List<Long> {
        if (count <= 0) return emptyList()
        if (durationMs <= 0) return listOf(0L)
        return (0 until count).map { i -> ((2 * i + 1) * durationMs * 1000L) / (2L * count) }
    }

    /** `count` indices spread evenly over `total` frames (all of them when there are fewer). */
    fun spread(total: Int, count: Int): List<Int> {
        if (total <= 0 || count <= 0) return emptyList()
        if (total <= count) return (0 until total).toList()
        return (0 until count).map { i -> ((2 * i + 1) * total) / (2 * count) }
    }

    /** At or above the category's threshold. */
    fun over(score: SensitiveScore?, thresholds: Map<Category, Int>): Boolean =
        score != null && score.score >= (thresholds[score.category] ?: ImagePolicy.DEFAULT_THRESHOLD)

    /** The clip's score: the one furthest above (or least below) its category's threshold. */
    fun top(scores: List<SensitiveScore?>, thresholds: Map<Category, Int> = emptyMap()): SensitiveScore? =
        scores.filterNotNull().maxByOrNull { it.score - (thresholds[it.category] ?: ImagePolicy.DEFAULT_THRESHOLD) }
}
