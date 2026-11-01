package dev.eziedutech.dcai.guardian.ingest

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Parity checks for the on-device stage 1 prompt and the coded-answer parsing. The prompt and
 * the label<->letter codebook must match code/distill/ondevice/build_short.py so the phone
 * decodes what the model was trained to emit. No native runtime here.
 */
class Stage1PromptTest {

    @Test
    fun shortPromptMatchesTheTrainingPrompt() {
        assertTrue(Stage1Prompt.SHORT_SYSTEM.startsWith("Label one chat message for child safety"))
        assertTrue(Stage1Prompt.SHORT_SYSTEM.contains("A=membangun_kedekatan"))
        assertTrue(Stage1Prompt.SHORT_SYSTEM.contains("Examples: BC4, N0, G7"))
    }

    @Test
    fun promptCarriesTheChatTemplateAndPreamble() {
        val p = Stage1Prompt.build("contact", "halo")
        assertTrue(p.startsWith("<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"))
        assertTrue(p.contains("Cutting Knowledge Date: December 2023\n"))
        assertTrue(p.contains("<|start_header_id|>user<|end_header_id|>\n\n{\"sender\": \"contact\", \"text\": \"halo\"}<|eot_id|>"))
        assertTrue(p.endsWith("<|start_header_id|>assistant<|end_header_id|>\n\n"))
    }

    @Test
    fun userPayloadEscapesLikePythonJsonDumps() {
        assertEquals(
            "{\"sender\": \"child\", \"text\": \"a\\\"b\\\\c\\nd\"}",
            Stage1Prompt.userPayload("child", "a\"b\\c\nd"),
        )
        assertTrue(Stage1Prompt.userPayload("contact", "x").contains("\"sender\": \"contact\""))
    }

    @Test
    fun parseDecodesLabelLettersAndSignal() {
        val r = Stage1Prompt.parse("BC4")
        assertEquals(listOf("meminta_kerahasiaan", "pindah_kanal"), r?.labels)
        assertEquals(40, r?.signal)
    }

    @Test
    fun parseNoneIsEmptyWithZeroSignal() {
        val r = Stage1Prompt.parse("N0")
        assertEquals(emptyList<String>(), r?.labels)
        assertEquals(0, r?.signal)
    }

    @Test
    fun parseTakesLastLineAndIsLenient() {
        val r = Stage1Prompt.parse("some preamble text\n g7 ")
        assertEquals(listOf("menekan_mengancam"), r?.labels)
        assertEquals(70, r?.signal)
    }

    @Test
    fun parseReturnsNullWhenNoCode() {
        assertNull(Stage1Prompt.parse("not a code"))
        assertNull(Stage1Prompt.parse("BC")) // no signal digit
    }

    @Test
    fun applyRulesStripApproachOnChildButKeepThreat() {
        val labels = Stage1Prompt.applyRules(
            "child",
            listOf("pindah_kanal", "menekan_mengancam", "kata_kasar"),
            hasFindings = false,
        )
        assertFalse(labels.contains("pindah_kanal"))
        assertTrue(labels.contains("menekan_mengancam"))
        assertTrue(labels.contains("kata_kasar"))
    }

    @Test
    fun applyRulesAddsPersonalDataOnChildFinding() {
        val labels = Stage1Prompt.applyRules("child", emptyList(), hasFindings = true)
        assertTrue(labels.contains("berbagi_data_pribadi"))
    }

    @Test
    fun applyRulesLeavesContactApproachAlone() {
        val labels = Stage1Prompt.applyRules("contact", listOf("pindah_kanal"), hasFindings = false)
        assertTrue(labels.contains("pindah_kanal"))
    }

    @Test
    fun hasFindingsDetectsMaskMarkers() {
        assertTrue(Stage1Prompt.hasFindings("ini alamatku [ALAMAT], main ke sini"))
        assertFalse(Stage1Prompt.hasFindings("besok ada PR matematika?"))
    }
}
