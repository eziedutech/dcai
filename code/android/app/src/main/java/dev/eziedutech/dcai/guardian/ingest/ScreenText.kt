package dev.eziedutech.dcai.guardian.ingest

/**
 * The parts of reading screen text that need no Android framework, so they can be tested on
 * the JVM. The accessibility service turns a window's node tree into these simple inputs,
 * then this decides what counts as a message the child sent or received.
 *
 * Nothing here masks or sends: callers pass the result to [MessageIngest], which masks on
 * the phone before anything leaves.
 */
class ScreenText(private val keep: Int = 400) {
    // The editable field's text per app, so that a non-empty value becoming empty (the app
    // cleared the field on send) tells us what the child just sent, with any keyboard.
    private val composing = HashMap<String, String>()
    // Transcript line keys already emitted, so each visible line is sent at most once.
    private val seen = LinkedHashMap<String, Boolean>()

    /**
     * The child's own typing, returned when the field is cleared after holding real text.
     * Returns the text that was just sent, or null. Works with any keyboard, not only the
     * dcAI one, which is the capability the dcAI keyboard alone cannot give.
     */
    fun onEditable(pkg: String, current: String): String? {
        val prev = composing[pkg].orEmpty()
        val now = current.trim()
        composing[pkg] = now
        if (now.isEmpty() && prev.length >= MIN) return prev
        return null
    }

    /** Clear the remembered field for an app, e.g. when its window goes away. */
    fun forget(pkg: String) {
        composing.remove(pkg)
    }

    /**
     * The transcript lines in a thread that have not been seen before, each returned once.
     * The caller passes the visible message lines; short fragments (clocks, counters, button
     * labels) and repeats are dropped. The editable field's own text is excluded by the
     * caller so a line is not counted as both typed and received.
     */
    fun newLines(pkg: String, thread: String, lines: List<String>): List<String> {
        val out = ArrayList<String>()
        for (raw in lines) {
            val line = raw.trim()
            if (line.length < MIN) continue
            val key = "$pkg|$thread|${line.hashCode()}"
            if (seen.put(key, true) == null) out.add(line)
        }
        while (seen.size > keep) {
            val it = seen.keys.iterator()
            it.next()
            it.remove()
        }
        return out
    }

    companion object {
        /** Ignore fragments shorter than this: timestamps, single letters, UI chrome. */
        const val MIN = 3

        // System UI, keyboards/IMEs and launchers are not conversations; reading them made
        // junk threads (e.g. "systemui", "latin") and needless load on the backend. Skip them.
        private val NOISE_APPS = setOf("android", "com.android.systemui", "com.android.settings")
        private val NOISE_SUBSTRINGS =
            listOf("inputmethod", "latin", "gboard", "swiftkey", ".ime", "launcher", "systemui")

        /** Whether an app package is system/keyboard/launcher chrome rather than a chat. */
        fun isNoiseApp(pkg: String): Boolean =
            pkg in NOISE_APPS || NOISE_SUBSTRINGS.any { pkg.contains(it, ignoreCase = true) }
    }
}
