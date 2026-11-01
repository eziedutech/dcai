package dev.eziedutech.dcai.guardian.ingest

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Parity checks for the on-device stage 1 prompt, parsing and rules. These must match the
 * server (code/backpy/app/risk/stage1.py) and the offline eval (code/distill/ondevice/eval_pte.py)
 * so the phone labels the same way the model was trained and measured. No native runtime here.
 */
class Stage1PromptTest {

    @Test
    fun systemPromptIsTheExactServerPrompt() {
        // Length pinned so an accidental edit here is caught (stage1.py SYSTEM is 2549 chars).
        assertEquals(2549, Stage1Prompt.SYSTEM.length)
        assertTrue(Stage1Prompt.SYSTEM.startsWith("You label ONE chat message"))
        assertTrue(Stage1Prompt.SYSTEM.contains("membangun_kedekatan"))
    }

    @Test
    fun promptCarriesTheChatTemplateAndPreamble() {
        val p = Stage1Prompt.build("contact", "halo")
        assertTrue(p.startsWith("<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"))
        // The Llama 3.2 template's own preamble was present in training; keep it.
        assertTrue(p.contains("Cutting Knowledge Date: December 2023\n"))
        assertTrue(p.contains("Today Date: "))
        assertTrue(p.contains("<|start_header_id|>user<|end_header_id|>\n\n{\"sender\": \"contact\", \"text\": \"halo\"}<|eot_id|>"))
        assertTrue(p.endsWith("<|start_header_id|>assistant<|end_header_id|>\n\n"))
    }

    @Test
    fun userPayloadEscapesLikePythonJsonDumps() {
        assertEquals(
            "{\"sender\": \"child\", \"text\": \"a\\\"b\\\\c\\nd\"}",
            Stage1Prompt.userPayload("child", "a\"b\\c\nd"),
        )
        // Any sender other than "child" is the contact side.
        assertTrue(Stage1Prompt.userPayload("contact", "x").contains("\"sender\": \"contact\""))
    }

    @Test
    fun parseReadsLabelsAndSignal() {
        val r = Stage1Prompt.parse("{\"labels\": [\"pindah_kanal\"], \"signal\": 40}")
        assertEquals(listOf("pindah_kanal"), r?.labels)
        assertEquals(40, r?.signal)
    }

    @Test
    fun parseTakesTheLastJsonLineAndDefaultsSignal() {
        val r = Stage1Prompt.parse("some preamble\n{\"labels\": []}")
        assertEquals(emptyList<String>(), r?.labels)
        assertEquals(0, r?.signal)
    }

    @Test
    fun parseReturnsNullWhenNothingValid() {
        assertNull(Stage1Prompt.parse("not json at all"))
        assertNull(Stage1Prompt.parse("{\"signal\": 10}")) // labels missing
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
