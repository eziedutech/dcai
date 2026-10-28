package dev.eziedutech.dcai.guardian.sites

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.nio.ByteBuffer

class SitesTest {
    // Built by the server's encoder (code/backpy/app/blocklist/lists.py); see data/sites/README.md.
    private val parity by lazy { SiteList("judi", ByteBuffer.wrap(File("../../../data/sites/parity.bin").readBytes())) }

    @Test
    fun phoneFindsWhatTheServerListed() {
        assertEquals(3, parity.count)
        val matcher = SiteMatcher(listOf(parity), allowed = emptySet())
        assertEquals(SiteMatch("judi", "casino-contoh.test"), matcher.match("casino-contoh.test"))
        assertEquals(SiteMatch("judi", "slot-contoh.test"), matcher.match("cdn.m.slot-contoh.test."))
        assertEquals(SiteMatch("judi", "judi-contoh.test"), matcher.match("WWW.Judi-Contoh.test"))
        assertNull(matcher.match("contoh.test"))
        assertNull(matcher.match("example.com"))
        assertNull(matcher.match("10.0.0.1"))
    }

    @Test
    fun allowedSiteIsNeverHeld() {
        val allowed = setOf(SiteMatcher.hex(SiteNames.hash("slot-contoh.test")))
        val matcher = SiteMatcher(listOf(parity), allowed)
        assertNull(matcher.match("cdn.slot-contoh.test"))
        assertNotNull(matcher.match("casino-contoh.test"))
    }

    @Test
    fun suffixesStopAtTwoLabels() {
        assertEquals(listOf("a.b.example.com", "b.example.com", "example.com"), SiteNames.suffixes("a.b.example.com"))
    }

    private fun query(name: String, id: Int = 0x1234): ByteArray {
        val qname = name.split('.').flatMap { listOf(it.length.toByte()) + it.toByteArray().toList() } + listOf(0.toByte())
        // Header: id, RD set, 1 question, 1 additional (an EDNS OPT record).
        val header = listOf(id shr 8, id, 0x01, 0x00, 0, 1, 0, 0, 0, 0, 0, 1).map { it.toByte() }
        val question = qname + listOf(0, 1, 0, 1).map { it.toByte() }
        val opt = listOf(0, 0, 41, 16, 0, 0, 0, 0, 0, 0, 0).map { it.toByte() }
        val dns = (header + question + opt).toByteArray()
        val udp = byteArrayOf(0x9c.toByte(), 0x40, 0, 53, 0, (8 + dns.size).toByte(), 0, 0) + dns
        val ip = ByteArray(20)
        ip[0] = 0x45
        ip[2] = ((20 + udp.size) shr 8).toByte(); ip[3] = (20 + udp.size).toByte()
        ip[8] = 64; ip[9] = 17
        byteArrayOf(10, 111, 222.toByte(), 2).copyInto(ip, 12)
        byteArrayOf(10, 111, 222.toByte(), 1).copyInto(ip, 16)
        return ip + udp
    }

    @Test
    fun parsesTheQuestionName() {
        val q = DnsQuery.parse(query("casino-contoh.test"))!!
        assertEquals("casino-contoh.test", q.name)
        assertEquals(0x12, q.dns[0].toInt())
    }

    @Test
    fun ignoresWhatIsNotADnsQuestion() {
        val tcp = query("a.test").also { it[9] = 6 }
        val otherPort = query("a.test").also { it[23] = 80 }
        assertNull(DnsQuery.parse(tcp))
        assertNull(DnsQuery.parse(otherPort))
        assertNull(DnsQuery.parse(ByteArray(10)))
    }

    @Test
    fun nxdomainAnswersTheSameQuestionBackToTheAsker() {
        val packet = query("casino-contoh.test")
        val reply = DnsQuery.parse(packet)!!.nxdomain()
        // Addresses and ports swapped.
        assertArrayEquals(packet.copyOfRange(16, 20), reply.copyOfRange(12, 16))
        assertArrayEquals(packet.copyOfRange(12, 16), reply.copyOfRange(16, 20))
        assertEquals(53, ((reply[20].toInt() and 0xff) shl 8) or (reply[21].toInt() and 0xff))
        // A valid IPv4 header checksum sums to zero.
        assertEquals(0, DnsQuery.checksum(reply, 0, 20))
        val dns = reply.copyOfRange(28, reply.size)
        assertEquals(0x12, dns[0].toInt())
        assertTrue((dns[2].toInt() and 0x80) != 0) // response
        assertEquals(3, dns[3].toInt() and 0x0f) // NXDOMAIN
        assertEquals(1, dns[5].toInt()) // the question stays
        assertEquals(0, dns[11].toInt()) // no OPT record copied
        assertEquals("casino-contoh.test", DnsQuery.parse(query("casino-contoh.test"))!!.name)
        // Total and UDP lengths agree with the bytes.
        assertEquals(reply.size, ((reply[2].toInt() and 0xff) shl 8) or (reply[3].toInt() and 0xff))
        assertEquals(reply.size - 20, ((reply[24].toInt() and 0xff) shl 8) or (reply[25].toInt() and 0xff))
    }
}
