package dev.eziedutech.dcai.guardian.vision

import dev.eziedutech.dcai.guardian.privacy.Pin
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The rules for one image. The sensitive-image model is a stand-in score here: no sensitive
 * image is created or used to test dcAI, so these tests check the mechanism around a model.
 */
class ImagePolicyTest {
    private val face = Box(0.1f, 0.1f, 0.4f, 0.5f)
    private val line = Box(0.0f, 0.6f, 1.0f, 0.7f)

    private fun sensitive(score: Int, category: Category = Category.SEKSUAL) =
        Findings(sensitive = SensitiveScore(category, score, "stand-in-model"), detectorVersion = "det")

    @Test
    fun sensitiveAtThresholdBlursWholeImage() {
        val d = ImagePolicy.decide(Trigger.PERCAKAPAN, sensitive(70))
        assertEquals(Category.SEKSUAL, d.category)
        assertEquals(Action.DIKABURKAN, d.action)
        assertTrue(d.blurAll)
        assertEquals("stand-in-model", d.modelVersion)
        assertTrue(d.signal)
    }

    @Test
    fun sensitiveBelowThresholdIsLeft() {
        val d = ImagePolicy.decide(Trigger.PERCAKAPAN, sensitive(69))
        assertEquals(Category.AMAN, d.category)
        assertEquals(Action.DIBIARKAN, d.action)
        assertFalse(d.signal)
    }

    @Test
    fun raisedThresholdAppliesPerCategory() {
        val thresholds = mapOf(Category.SEKSUAL to 74)
        assertEquals(Category.AMAN, ImagePolicy.decide(Trigger.PERCAKAPAN, sensitive(72), thresholds).category)
        assertEquals(Category.KEKERASAN, ImagePolicy.decide(Trigger.PERCAKAPAN, sensitive(72, Category.KEKERASAN), thresholds).category)
    }

    @Test
    fun confirmedFalseDetectionIsNotBlurredAgain() {
        val d = ImagePolicy.decide(Trigger.PERCAKAPAN, sensitive(95), confirmedFalse = setOf(Category.SEKSUAL))
        assertEquals(Category.AMAN, d.category)
    }

    @Test
    fun personalTextBlursOnlyItsRegions() {
        val d = ImagePolicy.decide(Trigger.DIBAGIKAN, Findings(personalText = listOf(line), faces = listOf(face), detectorVersion = "det"))
        assertEquals(Category.TEKS_PRIBADI, d.category)
        assertFalse(d.blurAll)
        assertEquals(listOf(line), d.regions)
    }

    @Test
    fun sensitiveWinsOverPersonalText() {
        val f = sensitive(90).copy(personalText = listOf(line))
        assertEquals(Category.SEKSUAL, ImagePolicy.decide(Trigger.DIBAGIKAN, f).category)
    }

    @Test
    fun facesAreBlurredOnlyWhenTheChildShares() {
        val f = Findings(faces = listOf(face), detectorVersion = "det")
        val shared = ImagePolicy.decide(Trigger.DIBAGIKAN, f)
        assertEquals(Category.WAJAH, shared.category)
        assertEquals(listOf(face), shared.regions)
        assertEquals(Category.AMAN, ImagePolicy.decide(Trigger.PERCAKAPAN, f).category)
    }

    @Test
    fun noModelMeansOnlyFacesAndText() {
        assertEquals(Category.AMAN, ImagePolicy.decide(Trigger.PERCAKAPAN, Findings(detectorVersion = "det")).category)
    }

    @Test
    fun thresholdRisesInSmallCappedSteps() {
        var t: Int? = null
        repeat(20) { t = LocalTuning.raised(t, Category.SEKSUAL) }
        assertEquals(ImagePolicy.DEFAULT_THRESHOLD + LocalTuning.MAX_RAISE, t)
        assertEquals(ImagePolicy.DEFAULT_THRESHOLD + LocalTuning.STEP, LocalTuning.raised(null, Category.KEKERASAN))
        // Text and face rules are not score based; their threshold does not move.
        assertEquals(ImagePolicy.DEFAULT_THRESHOLD, LocalTuning.raised(null, Category.TEKS_PRIBADI))
    }

    @Test
    fun nearIdenticalImageMatchesAConfirmedHash() {
        val gradient = IntArray(ImageHash.WIDTH * ImageHash.HEIGHT) { i -> (i * 37) % 256 }
        val base = ImageHash.dHash(gradient)
        val nudged = ImageHash.dHash(gradient.copyOf().also { it[5] = (it[5] + 3) % 256 })
        val other = ImageHash.dHash(IntArray(gradient.size) { i -> 255 - gradient[i] })
        val confirmed = listOf(base to Category.SEKSUAL)
        assertEquals(setOf(Category.SEKSUAL), LocalTuning.matches(nudged, confirmed))
        assertTrue(LocalTuning.matches(other, confirmed).isEmpty())
    }

    @Test
    fun hashRoundTripsThroughHex() {
        for (h in listOf(0L, -1L, Long.MIN_VALUE, 0x0123456789abcdefL)) {
            assertEquals(h, ImageHash.fromHex(ImageHash.toHex(h)))
            assertEquals(16, ImageHash.toHex(h).length)
        }
    }

    @Test
    fun ocrBlursLinesWithPersonalData() {
        val phone = OcrLine("HP 0812-3456-7890", Box(0f, 0.5f, 1f, 0.6f))
        val title = OcrLine("KARTU PELAJAR", Box(0f, 0f, 1f, 0.1f))
        val block = OcrBlock("KARTU PELAJAR\nHP 0812-3456-7890", Box(0f, 0f, 1f, 0.6f), listOf(title, phone))
        assertEquals(listOf(phone.box), OcrText.personalRegions(listOf(block)))
    }

    @Test
    fun ocrBlursWholeBlockWhenDataSpansLines() {
        // Neither line is an address on its own; the block, joined by a line break, is.
        val a = OcrLine("Jl.", Box(0f, 0f, 1f, 0.1f))
        val b = OcrLine("Mawar No. 12", Box(0f, 0.1f, 1f, 0.2f))
        val block = OcrBlock("Jl.\nMawar No. 12", Box(0f, 0f, 1f, 0.2f), listOf(a, b))
        assertEquals(listOf(block.box), OcrText.personalRegions(listOf(block)))
    }

    @Test
    fun ocrWithoutPersonalDataBlursNothing() {
        val block = OcrBlock("GG WP", Box(0f, 0f, 1f, 1f), listOf(OcrLine("GG WP", Box(0f, 0f, 1f, 1f))))
        assertTrue(OcrText.personalRegions(listOf(block)).isEmpty())
    }

    @Test
    fun knownNameInImageIsPersonal() {
        val line = OcrLine("Nama: Kit", Box(0f, 0f, 1f, 0.1f))
        val block = OcrBlock(line.text, line.box, listOf(line))
        assertEquals(listOf(line.box), OcrText.personalRegions(listOf(block), listOf("Kit")))
    }

    @Test
    fun ocrMisreadStreetPrefixIsStillAnAddress() {
        for (misread in listOf("JI. Mawar No. 12", "J1. Mawar No. 12", "JIn Mawar No. 12")) {
            val line = OcrLine(misread, Box(0f, 0f, 1f, 0.1f))
            assertEquals(misread, listOf(line.box), OcrText.personalRegions(listOf(OcrBlock(misread, line.box, listOf(line)))))
        }
        // Words that merely start with "JI" are left alone.
        assertEquals("JIKA nanti", OcrText.normalize("JIKA nanti"))
    }

    @Test
    fun pinIsHashedAndChecked() {
        val salt = Pin.newSalt()
        val hash = Pin.hash("4821", salt)
        assertTrue(Pin.matches("4821", salt, hash))
        assertFalse(Pin.matches("4822", salt, hash))
        assertFalse(Pin.valid("12a4"))
        assertFalse(Pin.valid("123"))
        assertFalse(Pin.matches("482", salt, hash))
    }
}
