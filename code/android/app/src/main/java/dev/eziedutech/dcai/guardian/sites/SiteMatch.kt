package dev.eziedutech.dcai.guardian.sites

import java.nio.ByteBuffer
import java.security.MessageDigest

/**
 * Site names and the list format made by code/backpy/app/blocklist/lists.py: the sorted
 * first 5 bytes of SHA-256 over each normalised domain. The same rules on both sides, so a
 * name the server listed is the name the phone finds. Pure Kotlin, tested without a phone.
 */
object SiteNames {
    const val HASH_BYTES = 5
    private val IPV4 = Regex("""^[0-9]{1,3}(\.[0-9]{1,3}){3}$""")

    fun normalise(name: String): String? {
        var d = name.trim().lowercase().trimStart('.').trimEnd('.')
        if (d.startsWith("www.")) d = d.substring(4)
        if (d.isEmpty() || '.' !in d || '/' in d || ' ' in d || d.length > 253) return null
        if (IPV4.matches(d) || ':' in d) return null
        return d
    }

    fun hash(domain: String): ByteArray =
        MessageDigest.getInstance("SHA-256").digest(domain.toByteArray(Charsets.UTF_8)).copyOf(HASH_BYTES)

    /** The name, then each parent domain down to two labels: a.b.example.com, b.example.com, example.com. */
    fun suffixes(domain: String): List<String> {
        val labels = domain.split('.')
        return (0 until labels.size - 1).map { labels.subList(it, labels.size).joinToString(".") }
    }
}

/** One category's list, read from a buffer (memory-mapped on the phone). */
class SiteList(val name: String, private val buf: ByteBuffer) {
    val count: Int

    init {
        val magic = ByteArray(4) { buf.get(it) }
        require(magic.contentEquals(MAGIC)) { "not a dcAI site list" }
        require(buf.get(4).toInt() == FORMAT) { "unknown site list format" }
        count = buf.getInt(5)
        require(count >= 0 && buf.capacity().toLong() == HEADER + count.toLong() * SiteNames.HASH_BYTES) { "site list size mismatch" }
    }

    fun containsHash(target: ByteArray): Boolean {
        var lo = 0
        var hi = count
        while (lo < hi) {
            val mid = (lo + hi) ushr 1
            val c = compareAt(HEADER + mid * SiteNames.HASH_BYTES, target)
            when {
                c < 0 -> lo = mid + 1
                c > 0 -> hi = mid
                else -> return true
            }
        }
        return false
    }

    private fun compareAt(offset: Int, target: ByteArray): Int {
        for (i in 0 until SiteNames.HASH_BYTES) {
            val a = buf.get(offset + i).toInt() and 0xff
            val b = target[i].toInt() and 0xff
            if (a != b) return a - b
        }
        return 0
    }

    companion object {
        val MAGIC = "DCBL".toByteArray(Charsets.US_ASCII)
        const val FORMAT = 1
        const val HEADER = 9
    }
}

/** What a looked-up name matched: the category, and the listed (parent) domain. */
data class SiteMatch(val category: String, val listed: String)

/**
 * The phone's lists plus the sites the parent allowed. Allowed wins: a site the parent
 * allowed with the PIN is never held again on this phone.
 */
class SiteMatcher(private val lists: List<SiteList>, private val allowed: Set<String>) {
    fun match(name: String): SiteMatch? {
        val domain = SiteNames.normalise(name) ?: return null
        val suffixes = SiteNames.suffixes(domain)
        val hashes = suffixes.map { SiteNames.hash(it) }
        if (hashes.any { hex(it) in allowed }) return null
        for (list in lists) {
            hashes.forEachIndexed { i, h -> if (list.containsHash(h)) return SiteMatch(list.name, suffixes[i]) }
        }
        return null
    }

    companion object {
        fun hex(bytes: ByteArray): String = bytes.joinToString("") { "%02x".format(it) }
    }
}
