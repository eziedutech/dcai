package dev.eziedutech.dcai.guardian.privacy

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/** The same cases the server's masking passes (code/backpy/tests/test_privacy_mask.py). */
class MaskTest {
    private val cases: List<JsonObject> by lazy {
        // Unit tests run from the module directory: code/android/app.
        val file = File("../../../data/privacy/pii_cases.json")
        Json.parseToJsonElement(file.readText()).jsonObject["cases"]!!.jsonArray.map { it.jsonObject }
    }

    @Test
    fun sharedCasesMatchTheServer() {
        val failures = cases.mapNotNull { case ->
            val text = case["text"]!!.jsonPrimitive.content
            val names = case["known_names"]?.jsonArray?.map { it.jsonPrimitive.content } ?: emptyList()
            val expect = case["expect"]!!.jsonArray.map { it.jsonPrimitive.content }.toSortedSet()
            val found = Mask.find(text, names).map { it.kind.name }.toSortedSet()
            if (found != expect) "$text: expected $expect, found $found" else null
        }
        assertTrue("${failures.size} of ${cases.size} cases differ:\n" + failures.joinToString("\n"), failures.isEmpty())
        assertTrue(cases.size >= 50)
    }

    @Test
    fun maskReplacesValuesWithMarkers() {
        val m = Mask.mask("hai Kit, wa aku 0812-0000-1234 atau kit@example.com", listOf("Kit"))
        assertEquals("hai [NAMA], wa aku [TELEPON] atau [EMAIL]", m.text)
        assertFalse(m.text.contains("0812"))
        assertEquals(setOf(Kind.NAMA, Kind.TELEPON, Kind.EMAIL), m.kinds)
    }

    @Test
    fun luhn() {
        assertTrue(Mask.luhnOk("4111111111111111"))
        assertFalse(Mask.luhnOk("4111111111111112"))
    }
}
