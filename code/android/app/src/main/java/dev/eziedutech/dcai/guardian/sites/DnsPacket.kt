package dev.eziedutech.dcai.guardian.sites

/**
 * The few packet shapes the DNS-only VPN handles: an IPv4 UDP datagram to port 53 carrying
 * one DNS question. Everything else is not routed into the VPN at all. Pure Kotlin.
 */
class DnsQuery private constructor(
    /** The whole IPv4 packet as read from the VPN interface. */
    val packet: ByteArray,
    private val ipHeaderLength: Int,
    /** Offset of the DNS message inside the packet. */
    val dnsOffset: Int,
    val dnsLength: Int,
    /** End of the question section, relative to the DNS message. */
    private val questionEnd: Int,
    val name: String,
) {
    val dns: ByteArray get() = packet.copyOfRange(dnsOffset, dnsOffset + dnsLength)

    /** "No such domain" for this question, as an IPv4 packet back to the asker. */
    fun nxdomain(): ByteArray {
        val reply = packet.copyOfRange(dnsOffset, dnsOffset + questionEnd)
        val flags = ((reply[2].toInt() and 0xff) shl 8) or (reply[3].toInt() and 0xff)
        // QR=1, keep opcode and RD, RA=1, RCODE=3 (NXDOMAIN).
        val out = 0x8000 or (flags and 0x7900) or 0x0080 or 0x0003
        reply[2] = (out shr 8).toByte()
        reply[3] = out.toByte()
        // One question, no answer, authority or additional records (drops any EDNS OPT).
        for (i in 6 until 12) reply[i] = 0
        return reply(reply)
    }

    /** Wraps a DNS reply from the upstream resolver into an IPv4 packet back to the asker. */
    fun reply(dnsReply: ByteArray): ByteArray {
        val ipLen = 20
        val total = ipLen + 8 + dnsReply.size
        val out = ByteArray(total)
        out[0] = 0x45 // IPv4, 20-byte header
        put16(out, 2, total)
        out[8] = 64 // TTL
        out[9] = 17 // UDP
        // Addresses and ports swapped: the reply comes from the address the app asked.
        System.arraycopy(packet, 16, out, 12, 4)
        System.arraycopy(packet, 12, out, 16, 4)
        put16(out, 10, checksum(out, 0, ipLen))
        val udp = ipHeaderLength
        out[ipLen] = packet[udp + 2]
        out[ipLen + 1] = packet[udp + 3]
        out[ipLen + 2] = packet[udp]
        out[ipLen + 3] = packet[udp + 1]
        put16(out, ipLen + 4, 8 + dnsReply.size)
        // UDP checksum 0: allowed for IPv4 and accepted by the phone's resolver.
        System.arraycopy(dnsReply, 0, out, ipLen + 8, dnsReply.size)
        return out
    }

    companion object {
        /** A DNS question in an IPv4 UDP packet to port 53, or null for anything else. */
        fun parse(packet: ByteArray, length: Int = packet.size): DnsQuery? {
            if (length < 20 + 8 + 12) return null
            if ((packet[0].toInt() ushr 4) != 4) return null
            val ihl = (packet[0].toInt() and 0x0f) * 4
            if (ihl < 20 || packet[9].toInt() != 17) return null
            val dstPort = get16(packet, ihl + 2)
            if (dstPort != 53) return null
            val udpLength = get16(packet, ihl + 4)
            val dnsOffset = ihl + 8
            val dnsLength = minOf(udpLength - 8, length - dnsOffset)
            if (dnsLength < 12) return null
            val questions = get16(packet, dnsOffset + 4)
            if (questions != 1) return null
            // Read the question name: length-prefixed labels, no compression in a query.
            val labels = mutableListOf<String>()
            var pos = dnsOffset + 12
            val end = dnsOffset + dnsLength
            while (true) {
                if (pos >= end) return null
                val len = packet[pos].toInt() and 0xff
                if (len == 0) {
                    pos++
                    break
                }
                if (len > 63 || pos + 1 + len > end) return null
                labels += String(packet, pos + 1, len, Charsets.US_ASCII)
                pos += 1 + len
            }
            if (pos + 4 > end || labels.isEmpty()) return null
            return DnsQuery(
                packet.copyOf(length), ihl, dnsOffset, dnsLength,
                questionEnd = pos + 4 - dnsOffset, name = labels.joinToString("."),
            )
        }

        private fun get16(b: ByteArray, at: Int) = ((b[at].toInt() and 0xff) shl 8) or (b[at + 1].toInt() and 0xff)

        private fun put16(b: ByteArray, at: Int, v: Int) {
            b[at] = (v shr 8).toByte()
            b[at + 1] = v.toByte()
        }

        fun checksum(b: ByteArray, from: Int, len: Int): Int {
            var sum = 0L
            var i = from
            while (i < from + len) {
                sum += get16(b, i)
                i += 2
            }
            while (sum shr 16 != 0L) sum = (sum and 0xffff) + (sum shr 16)
            return sum.inv().toInt() and 0xffff
        }
    }
}
