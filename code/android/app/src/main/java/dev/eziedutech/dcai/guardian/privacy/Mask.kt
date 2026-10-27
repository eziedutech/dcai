package dev.eziedutech.dcai.guardian.privacy

/**
 * Personal data masking on the phone, before anything leaves it. A port of
 * code/backpy/app/privacy/mask.py with the same rules and the same shared test cases
 * (data/privacy/pii_cases.json), so the phone and the server agree on what is personal.
 * The server masks again; this copy is what keeps raw values on the phone.
 */
enum class Kind { TELEPON, EMAIL, KARTU, ALAMAT, AKUN, NAMA, SEKOLAH }

/** Where personal data was found. Holds no copy of the value. */
data class Finding(val kind: Kind, val start: Int, val end: Int)

data class Masked(val text: String, val findings: List<Finding>) {
    val kinds: Set<Kind> get() = findings.map { it.kind }.toSet()
}

object Mask {
    private val U = RegexOption.IGNORE_CASE

    // Python's re is Unicode-aware for \w, \d and \b; Java needs (?U) for the same.
    private fun rx(pattern: String, vararg options: RegexOption) =
        Regex("(?U)$pattern", options.toSet())

    private val EMAIL = rx("""[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}""")
    private val CARD = rx("""(?<![\d])(?:\d[ -]?){12,18}\d(?![\d])""")
    private val PHONE_ID = rx("""(?<![\d+])(?:\+62|62|0)[ -]?8\d(?:[ .-]?\d){7,10}(?![\d])""")
    private val PHONE_INTL = rx("""(?<![\w+])\+\d{1,3}(?:[ .-]?\d){8,12}(?![\d])""")
    private val CARD_EXPIRY = rx(
        """\b(?:exp(?:iry|ired)?|berlaku(?: s\.?d\.?| sampai)?)\.?:?\s*\d{2}\s*/\s*\d{2,4}\b""", U,
    )
    private val SCHOOL = rx(
        """\b(?:SD|SMP|SMA|SMK|MI|MTs|MA|SLB)N?\s+(?:Negeri\s+|Swasta\s+|IT\s+)?""" +
            """(?:[A-Z][\w'-]*|\d{1,3})(?:\s+(?:[A-Z][\w'-]*|\d{1,3})){0,3}""" +
            """(?:\s*,?\s*(?:kelas|class)\s+\d{1,2}\s?[A-Za-z]?\b)?""",
    )
    private val HANDLE = rx("""(?<![\w@])@[A-Za-z0-9_.]{3,30}\b""")
    private val STREET = rx(
        """\b(?:jl\.?|jln\.?|jalan)\s+(?:[A-Za-z][\w'.]*\s*){1,4}?""" +
            """(?:,?\s*(?:no\.?|nomor)\s*\d+[A-Za-z]?|,?\s*rt\.?\s*\d{1,3}(?:\s*/\s*rw\.?\s*\d{1,3})?)""" +
            """(?:\s*,?\s*rt\.?\s*\d{1,3}(?:\s*/\s*rw\.?\s*\d{1,3})?)?""",
        U,
    )
    private val STREET_SHORT = rx("""\b(?:jl|jln)\.?\s+[A-Za-z][\w'.]*(?:\s+[A-Z][\w'.]*){0,3}""", U)
    private val RT_RW = rx("""\brt\.?\s*\d{1,3}\s*/?\s*rw\.?\s*\d{1,3}\b""", U)
    private val NAME_INTRO = rx(
        """\b(?:nama\s?(?:ku|aku|saya|gue|gw)|my name is|panggil\s+(?:aku|saja|aja))""" +
            """\s+(?:adalah\s+|itu\s+)?([A-Za-z][a-z]{1,20})\b""",
        U,
    )
    private val NOT_NAMES = setOf("aja", "saja", "dong", "deh", "kok", "sih", "itu", "apa", "siapa", "is", "the")

    fun luhnOk(digits: String): Boolean {
        var total = 0
        digits.reversed().forEachIndexed { i, ch ->
            var d = ch.digitToInt()
            if (i % 2 == 1) {
                d *= 2
                if (d > 9) d -= 9
            }
            total += d
        }
        return total % 10 == 0
    }

    fun find(text: String, knownNames: List<String> = emptyList()): List<Finding> {
        val spans = mutableListOf<Finding>()
        fun add(kind: Kind, start: Int, end: Int) {
            if (spans.none { start < it.end && it.start < end }) spans += Finding(kind, start, end)
        }

        EMAIL.findAll(text).forEach { add(Kind.EMAIL, it.range.first, it.range.last + 1) }
        CARD.findAll(text).forEach {
            val digits = it.value.filter(Char::isDigit)
            if (digits.length in 13..19 && luhnOk(digits) && !PHONE_ID.matches(it.value)) {
                add(Kind.KARTU, it.range.first, it.range.last + 1)
            }
        }
        CARD_EXPIRY.findAll(text).forEach { add(Kind.KARTU, it.range.first, it.range.last + 1) }
        for (p in listOf(PHONE_ID, PHONE_INTL)) {
            p.findAll(text).forEach { add(Kind.TELEPON, it.range.first, it.range.last + 1) }
        }
        for (p in listOf(STREET, STREET_SHORT, RT_RW)) {
            p.findAll(text).forEach { add(Kind.ALAMAT, it.range.first, it.range.last + 1) }
        }
        SCHOOL.findAll(text).forEach { add(Kind.SEKOLAH, it.range.first, it.range.last + 1) }
        HANDLE.findAll(text).forEach { add(Kind.AKUN, it.range.first, it.range.last + 1) }
        NAME_INTRO.findAll(text).forEach { m ->
            val g = m.groups[1] ?: return@forEach
            if (g.value.lowercase() !in NOT_NAMES) add(Kind.NAMA, g.range.first, g.range.last + 1)
        }
        for (name in knownNames) {
            if (name.length < 2) continue
            Regex("(?U)(?<!\\w)${Regex.escape(name)}(?!\\w)", RegexOption.IGNORE_CASE)
                .findAll(text).forEach { add(Kind.NAMA, it.range.first, it.range.last + 1) }
        }
        return spans.sortedBy { it.start }
    }

    fun mask(text: String, knownNames: List<String> = emptyList()): Masked {
        val findings = find(text, knownNames)
        val out = StringBuilder()
        var pos = 0
        for (f in findings) {
            out.append(text, pos, f.start).append('[').append(f.kind.name).append(']')
            pos = f.end
        }
        out.append(text, pos, text.length)
        return Masked(out.toString(), findings)
    }
}
