package dev.eziedutech.dcai.guardian.screen

import android.app.AppOpsManager
import android.app.usage.UsageEvents
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.Intent
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.os.Process

/**
 * Which app is in front and for how long, from Android's usage access. dcAI reads app
 * names and times only, never what is inside an app, and the names stay on the phone.
 */
class UsageReader(private val context: Context) {
    private val usm = context.getSystemService(UsageStatsManager::class.java)
    private val categories = HashMap<String, AppCategory?>()

    fun hasPermission(): Boolean {
        val ops = context.getSystemService(AppOpsManager::class.java)
        val mode = ops.unsafeCheckOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS, Process.myUid(), context.packageName)
        return mode == AppOpsManager.MODE_ALLOWED
    }

    /** Foreground intervals between [from] and [to]; an app still open ends at [to]. */
    fun intervals(from: Long, to: Long, allowed: Set<String>): List<Interval> {
        val events = usm.queryEvents(from, to) ?: return emptyList()
        val open = HashMap<String, Long>()
        val out = mutableListOf<Interval>()
        val e = UsageEvents.Event()
        fun close(pkg: String, at: Long) {
            val start = open.remove(pkg) ?: return
            val cat = categoryOf(pkg, allowed) ?: return
            if (at > start) out += Interval(pkg, cat, start, at)
        }
        while (events.hasNextEvent()) {
            events.getNextEvent(e)
            when (e.eventType) {
                UsageEvents.Event.ACTIVITY_RESUMED -> {
                    // One app in front at a time: a new one closes the others.
                    open.keys.filter { it != e.packageName }.forEach { close(it, e.timeStamp) }
                    open.putIfAbsent(e.packageName, e.timeStamp)
                }
                UsageEvents.Event.ACTIVITY_PAUSED, UsageEvents.Event.ACTIVITY_STOPPED -> close(e.packageName, e.timeStamp)
                UsageEvents.Event.SCREEN_NON_INTERACTIVE, UsageEvents.Event.DEVICE_SHUTDOWN ->
                    open.keys.toList().forEach { close(it, e.timeStamp) }
            }
        }
        open.keys.toList().forEach { close(it, to) }
        return out.sortedBy { it.start }
    }

    /** The app in front now, if it counts toward time online. */
    fun foreground(intervals: List<Interval>, now: Long): Interval? =
        intervals.lastOrNull()?.takeIf { now - it.end < 3_000 }

    /**
     * The category an app counts in, or null for apps that never count: dcAI, the home
     * screen, system screens, calls, and apps the parent always allows.
     */
    fun categoryOf(pkg: String, allowed: Set<String>): AppCategory? {
        if (pkg in allowed) return null
        return categories.getOrPut(pkg) { lookup(pkg) }
    }

    private fun lookup(pkg: String): AppCategory? {
        if (pkg == context.packageName || pkg in NEVER || pkg == homePackage()) return null
        KNOWN[pkg]?.let { return it }
        val info = runCatching { context.packageManager.getApplicationInfo(pkg, 0) }.getOrNull() ?: return null
        return when (info.category) {
            ApplicationInfo.CATEGORY_VIDEO -> AppCategory.VIDEO
            ApplicationInfo.CATEGORY_GAME -> AppCategory.GAME
            ApplicationInfo.CATEGORY_SOCIAL -> AppCategory.SOSIAL
            // System parts without an icon (services, keyboards) do not count; a browser does.
            else -> if (info.flags and ApplicationInfo.FLAG_SYSTEM != 0 && !launchable(pkg)) null else AppCategory.LAIN
        }
    }

    private fun launchable(pkg: String) = context.packageManager.getLaunchIntentForPackage(pkg) != null

    private fun homePackage(): String? = runCatching {
        context.packageManager.resolveActivity(
            Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME), PackageManager.MATCH_DEFAULT_ONLY,
        )?.activityInfo?.packageName
    }.getOrNull()

    private companion object {
        /** Apps that do not declare a category but are short video or feeds. */
        val KNOWN = mapOf(
            "com.google.android.youtube" to AppCategory.VIDEO,
            "com.google.android.apps.youtube.music" to AppCategory.VIDEO,
            "com.zhiliaoapp.musically" to AppCategory.VIDEO, // TikTok
            "com.ss.android.ugc.trill" to AppCategory.VIDEO, // TikTok Lite / regional
            "com.ss.android.ugc.aweme" to AppCategory.VIDEO, // TikTok / Douyin
            "com.kwai.bulldog" to AppCategory.VIDEO, // SnackVideo
            "video.like" to AppCategory.VIDEO, // Likee
            "com.instagram.android" to AppCategory.SOSIAL, // Instagram, incl. Reels
            "com.instagram.barcelona" to AppCategory.SOSIAL, // Threads
            "com.facebook.katana" to AppCategory.SOSIAL, // Facebook, incl. Reels
            "com.facebook.lite" to AppCategory.SOSIAL, // Facebook Lite
            "com.snapchat.android" to AppCategory.SOSIAL,
            "com.twitter.android" to AppCategory.SOSIAL, // X
            "com.ss.android.ugc.tiktok" to AppCategory.VIDEO,
        )
        val NEVER = setOf(
            "com.android.systemui", "com.android.settings", "com.google.android.dialer", "com.android.dialer",
            "com.google.android.permissioncontroller", "com.android.permissioncontroller",
            "com.google.android.apps.nexuslauncher", "com.android.launcher3",
        )
    }
}
