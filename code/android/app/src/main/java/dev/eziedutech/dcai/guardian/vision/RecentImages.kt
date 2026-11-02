package dev.eziedutech.dcai.guardian.vision

/**
 * Pictures already reported per chat, so a picture that stays on screen across screenshots
 * gives one signal and one reminder. Memory only, hashes only (dHash), bounded.
 */
object RecentImages {
    const val WINDOW_MS = 24 * 60 * 60 * 1000L
    private const val MAX = 200

    private data class Seen(val key: String, val hash: Long, val at: Long)

    private val seen = ArrayDeque<Seen>()

    /** True the first time a picture is seen in this chat within the window, and records it. */
    @Synchronized
    fun firstTime(threadKey: String, hash: Long, now: Long): Boolean {
        seen.removeAll { now - it.at > WINDOW_MS }
        val again = seen.any {
            it.key == threadKey && ImageHash.distance(it.hash, hash) <= LocalTuning.SAME_IMAGE_DISTANCE
        }
        if (!again) {
            seen.addLast(Seen(threadKey, hash, now))
            while (seen.size > MAX) seen.removeFirst()
        }
        return !again
    }

    @Synchronized
    fun clear() = seen.clear()
}
