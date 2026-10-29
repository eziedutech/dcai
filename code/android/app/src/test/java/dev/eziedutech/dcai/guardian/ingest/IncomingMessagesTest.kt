package dev.eziedutech.dcai.guardian.ingest

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** The parts of reading chat notifications that need no Android framework. */
class IncomingMessagesTest {
    private fun msg(text: String, time: Long, thread: String = "Kak Bima") =
        IncomingMessage(thread, thread, text, time, group = false, fromChild = false, contactKnown = true)

    @Test
    fun aSenderShownAsANumberIsNotAKnownContact() {
        assertFalse(IncomingMessages.contactKnown("+62 812-3456-7890"))
        assertFalse(IncomingMessages.contactKnown("0812 3456 7890"))
        assertTrue(IncomingMessages.contactKnown("Kak Bima"))
        assertFalse(IncomingMessages.contactKnown(null))
    }

    @Test
    fun aRepeatedMessageIsSentOnce() {
        val first = msg("halo, kamu jago banget", 1_000)
        assertTrue(Seen.first("com.chat.test", first))
        assertFalse(Seen.first("com.chat.test", first))
        assertTrue(Seen.first("com.chat.test", msg("kirim foto dong", 2_000)))
        assertTrue(Seen.first("com.other.test", first))
    }

    @Test
    fun theKeyboardJoinsTheChatSeenInTheLastTenMinutes() {
        RecentThreads.note("com.chat.recent", "Kak Bima", now = 0)
        assertEquals("Kak Bima", RecentThreads.current("com.chat.recent", now = 9 * 60_000))
        assertNull(RecentThreads.current("com.chat.recent", now = 11 * 60_000))
        assertNull(RecentThreads.current("com.chat.none", now = 0))
    }
}
