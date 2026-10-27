package dev.eziedutech.dcai.guardian.vision

/**
 * How dcAI decides what to do with one image, from what the on-device detectors found.
 * Pure Kotlin, so the rules are unit tested without a phone. The image itself is never an
 * input here and never leaves the phone; only the decision's label reaches the server.
 */
enum class Trigger(val wire: String) {
    /** An image received in a conversation already at perhatian or above. */
    PERCAKAPAN("percakapan"),
    /** An image the child is about to share. */
    DIBAGIKAN("dibagikan"),
    /** An image on a flagged site. */
    SITUS("situs"),
}

/** Wire values match ImageCategory and ImageAction in code/backpy/app/api/devices.py. */
enum class Category(val wire: String) {
    SEKSUAL("seksual"),
    KEKERASAN("kekerasan"),
    TEKS_PRIBADI("teks_pribadi"),
    WAJAH("wajah"),
    AMAN("aman"),
}

enum class Action(val wire: String) { DIKABURKAN("dikaburkan"), DIBIARKAN("dibiarkan") }

/** A region of the image as fractions of its width and height (0..1). */
data class Box(val left: Float, val top: Float, val right: Float, val bottom: Float)

/** The sensitive-image model's top score for one category, 0..100. */
data class SensitiveScore(val category: Category, val score: Int, val modelVersion: String)

data class Findings(
    val faces: List<Box> = emptyList(),
    /** Text regions that hold personal data (phone, address, school, card, account). */
    val personalText: List<Box> = emptyList(),
    /** Null when no sensitive-image model is installed. */
    val sensitive: SensitiveScore? = null,
    val detectorVersion: String = "",
)

data class Decision(
    val category: Category,
    val action: Action,
    val score: Int,
    /** Blur the whole image (a sensitive image) instead of the regions. */
    val blurAll: Boolean,
    val regions: List<Box>,
    val modelVersion: String,
) {
    /** Only a non-safe label is worth a signal to the server. */
    val signal: Boolean get() = category != Category.AMAN

    companion object {
        fun leave(modelVersion: String = "") =
            Decision(Category.AMAN, Action.DIBIARKAN, 0, blurAll = false, regions = emptyList(), modelVersion = modelVersion)
    }
}

object ImagePolicy {
    /** Default score at which a sensitive category is blurred. */
    const val DEFAULT_THRESHOLD = 70

    /**
     * @param thresholds the phone's current threshold per sensitive category (tier 1 raises
     *   it a little after the parent confirms a false detection).
     * @param confirmedFalse categories the parent already marked as a false detection for an
     *   image that looks like this one (perceptual hash match).
     */
    fun decide(
        trigger: Trigger,
        findings: Findings,
        thresholds: Map<Category, Int> = emptyMap(),
        confirmedFalse: Set<Category> = emptySet(),
    ): Decision {
        val sensitive = findings.sensitive
        if (sensitive != null &&
            sensitive.category in SENSITIVE &&
            sensitive.category !in confirmedFalse &&
            sensitive.score >= (thresholds[sensitive.category] ?: DEFAULT_THRESHOLD)
        ) {
            return Decision(sensitive.category, Action.DIKABURKAN, sensitive.score, blurAll = true, regions = emptyList(), modelVersion = sensitive.modelVersion)
        }
        if (findings.personalText.isNotEmpty() && Category.TEKS_PRIBADI !in confirmedFalse) {
            return Decision(Category.TEKS_PRIBADI, Action.DIKABURKAN, 100, blurAll = false, regions = findings.personalText, modelVersion = findings.detectorVersion)
        }
        // A face matters when the child shares it; a face in a received image is the sender's.
        if (trigger == Trigger.DIBAGIKAN && findings.faces.isNotEmpty() && Category.WAJAH !in confirmedFalse) {
            return Decision(Category.WAJAH, Action.DIKABURKAN, 100, blurAll = false, regions = findings.faces, modelVersion = findings.detectorVersion)
        }
        return Decision.leave(sensitive?.modelVersion ?: findings.detectorVersion)
    }

    val SENSITIVE = setOf(Category.SEKSUAL, Category.KEKERASAN)
}

/**
 * Tier 1 of learning from a false detection, local to this phone. The parent confirms with
 * the PIN that a blurred image was fine. The image's perceptual hash is remembered so the
 * same or a near-identical image is not blurred again, and that category's threshold rises
 * by a small step, capped, so one confirmation never switches a category off.
 */
object LocalTuning {
    const val STEP = 2
    const val MAX_RAISE = 10
    /** Hamming distance at or below which two 64-bit dHashes count as the same picture. */
    const val SAME_IMAGE_DISTANCE = 6

    fun raised(current: Int?, category: Category): Int {
        val now = current ?: ImagePolicy.DEFAULT_THRESHOLD
        if (category !in ImagePolicy.SENSITIVE) return now
        return minOf(now + STEP, ImagePolicy.DEFAULT_THRESHOLD + MAX_RAISE)
    }

    fun matches(hash: Long, confirmed: List<Pair<Long, Category>>): Set<Category> =
        confirmed.filter { ImageHash.distance(it.first, hash) <= SAME_IMAGE_DISTANCE }.map { it.second }.toSet()
}

/** Difference hash (dHash): 64 bits from a 9x8 grayscale thumbnail, robust to resizing. */
object ImageHash {
    const val WIDTH = 9
    const val HEIGHT = 8

    /** @param gray luminance 0..255, row-major, WIDTH x HEIGHT. */
    fun dHash(gray: IntArray): Long {
        require(gray.size == WIDTH * HEIGHT) { "expected ${WIDTH * HEIGHT} pixels" }
        var hash = 0L
        var bit = 0
        for (y in 0 until HEIGHT) {
            for (x in 0 until WIDTH - 1) {
                if (gray[y * WIDTH + x] > gray[y * WIDTH + x + 1]) hash = hash or (1L shl bit)
                bit++
            }
        }
        return hash
    }

    fun distance(a: Long, b: Long): Int = java.lang.Long.bitCount(a xor b)

    fun toHex(hash: Long): String = java.lang.Long.toUnsignedString(hash, 16).padStart(16, '0')

    fun fromHex(hex: String): Long = java.lang.Long.parseUnsignedLong(hex, 16)
}
