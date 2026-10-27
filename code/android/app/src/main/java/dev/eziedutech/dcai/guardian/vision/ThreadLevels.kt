package dev.eziedutech.dcai.guardian.vision

import java.util.concurrent.ConcurrentHashMap

/**
 * The latest level of each conversation, from the live stream. A received image is only
 * looked at when its conversation is already at perhatian or above; images in an ordinary
 * chat are left alone. Kept in memory: after a restart the next level event fills it again.
 */
object ThreadLevels {
    private val ORDER = listOf("aman", "perhatian", "waspada", "mendesak")
    private val levels = ConcurrentHashMap<String, String>()

    fun update(threadKey: String, level: String) {
        if (level in ORDER) levels[threadKey] = level
    }

    fun atLeast(threadKey: String, level: String): Boolean {
        val current = levels[threadKey] ?: return false
        return ORDER.indexOf(current) >= ORDER.indexOf(level)
    }

    fun clear() = levels.clear()
}
