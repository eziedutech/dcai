package dev.eziedutech.dcai.guardian.ingest

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/** The parts of reading screen text that need no Android framework. */
class ScreenTextTest {
    private val pkg = "com.any.chat"

    @Test
    fun textIsSentWhenTheFieldIsClearedAfterTyping() {
        val s = ScreenText()
        assertNull(s.onEditable(pkg, "kirim"))
        assertNull(s.onEditable(pkg, "kirim foto dong"))
        assertEquals("kirim foto dong", s.onEditable(pkg, ""))
        // A second clear with nothing held sends nothing.
        assertNull(s.onEditable(pkg, ""))
    }

    @Test
    fun aFieldClearedWithOnlyAFragmentSendsNothing() {
        val s = ScreenText()
        assertNull(s.onEditable(pkg, "ok"))
        assertNull(s.onEditable(pkg, ""))
    }

    @Test
    fun eachTranscriptLineIsReturnedOnce() {
        val s = ScreenText()
        // "ok" is shorter than the minimum and dropped as chrome; the rest are returned.
        val first = s.newLines(pkg, "Kak Bima", listOf("halo apa kabar", "main yuk", "ok"))
        assertEquals(listOf("halo apa kabar", "main yuk"), first)
        // The same window re-read adds only the genuinely new line.
        val second = s.newLines(pkg, "Kak Bima", listOf("halo apa kabar", "main yuk", "kirim foto dong"))
        assertEquals(listOf("kirim foto dong"), second)
    }

    @Test
    fun threadsAndAppsAreKeptApart() {
        val s = ScreenText()
        assertEquals(listOf("halo apa kabar"), s.newLines(pkg, "Kak Bima", listOf("halo apa kabar")))
        assertEquals(listOf("halo apa kabar"), s.newLines(pkg, "Mama", listOf("halo apa kabar")))
        assertEquals(listOf("halo apa kabar"), s.newLines("com.other.app", "Kak Bima", listOf("halo apa kabar")))
    }
}
