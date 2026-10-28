package dev.eziedutech.dcai.guardian.screen

import dev.eziedutech.dcai.guardian.net.Bedtime
import dev.eziedutech.dcai.guardian.net.ScreenPolicy
import java.time.DayOfWeek
import java.time.LocalDateTime
import java.time.LocalTime

/**
 * Time online rules, pure Kotlin so they are tested without a phone. The phone counts app
 * use in foreground intervals; these functions turn them into totals and decide what the
 * child sees now: nothing, a gentle reminder, or a break screen.
 */
enum class AppCategory(val wire: String) { VIDEO("video"), GAME("game"), SOSIAL("sosial"), LAIN("lain") }

/** One stretch of one app in the foreground, in epoch milliseconds. */
data class Interval(val pkg: String, val category: AppCategory, val start: Long, val end: Long) {
    val minutes: Double get() = (end - start) / 60_000.0
}

data class DayTotals(
    val minutes: Map<AppCategory, Int>,
    val bedtimeMinutes: Int,
    val longestSession: Int,
) {
    val total: Int get() = minutes.values.sum()
}

enum class BlockReason { BEDTIME, DAILY, CATEGORY, SESSION }

sealed interface Verdict {
    data object Allow : Verdict
    data class Remind(val kind: RemindKind, val minutes: Int) : Verdict
    /** [untilMillis] is set for a session break, which ends by itself. */
    data class Block(val reason: BlockReason, val category: AppCategory?, val untilMillis: Long? = null) : Verdict
}

enum class RemindKind { WIND_DOWN, SESSION, TEN_MINUTES_LEFT }

object TimeRules {
    /** Short video and feeds: where a session without a break is counted. */
    val SESSION_CATEGORIES = setOf(AppCategory.VIDEO, AppCategory.SOSIAL)

    /** Two intervals of the same app closer than this belong to one session. */
    const val SESSION_GAP_MS = 2 * 60_000L

    fun isSchoolDay(policy: ScreenPolicy, day: DayOfWeek) = day.value in policy.schoolDays

    /** The bedtime in force at [now]. The night belongs to the evening it started on. */
    fun bedtimeAt(policy: ScreenPolicy, now: LocalDateTime): Bedtime? {
        val today = if (isSchoolDay(policy, now.dayOfWeek)) policy.bedtimeSchool else policy.bedtimeWeekend
        val yesterday = now.minusDays(1).dayOfWeek
        val last = if (isSchoolDay(policy, yesterday)) policy.bedtimeSchool else policy.bedtimeWeekend
        val t = now.toLocalTime()
        if (last.enabled && crossesMidnight(last) && t < time(last.end)) return last
        if (today.enabled && inWindow(today, t)) return today
        return null
    }

    fun inBedtime(policy: ScreenPolicy, now: LocalDateTime) = bedtimeAt(policy, now) != null

    /** Minutes from [now] until tonight's bedtime starts, or null when it is off. */
    fun minutesToBedtime(policy: ScreenPolicy, now: LocalDateTime): Int? {
        if (inBedtime(policy, now)) return 0
        val tonight = if (isSchoolDay(policy, now.dayOfWeek)) policy.bedtimeSchool else policy.bedtimeWeekend
        if (!tonight.enabled) return null
        val start = time(tonight.start)
        val t = now.toLocalTime()
        val diff = (start.toSecondOfDay() - t.toSecondOfDay()) / 60
        return if (diff >= 0) diff else null
    }

    fun dailyLimit(policy: ScreenPolicy, now: LocalDateTime): Int? =
        if (isSchoolDay(policy, now.dayOfWeek)) policy.dailyLimitSchool else policy.dailyLimitWeekend

    fun totals(intervals: List<Interval>, policy: ScreenPolicy?, zone: java.time.ZoneId): DayTotals {
        val minutes = AppCategory.entries.associateWith { 0.0 }.toMutableMap()
        var bedtime = 0.0
        for (i in intervals) {
            minutes[i.category] = minutes.getValue(i.category) + i.minutes
            if (policy != null) bedtime += bedtimeMinutes(i, policy, zone)
        }
        return DayTotals(
            minutes = minutes.mapValues { it.value.toInt() },
            bedtimeMinutes = bedtime.toInt(),
            longestSession = sessions(intervals).maxOfOrNull { it.second }?.toInt() ?: 0,
        )
    }

    /** (package, minutes) per continuous session in short video and feeds. */
    fun sessions(intervals: List<Interval>): List<Pair<String, Double>> {
        val out = mutableListOf<Pair<String, Double>>()
        var pkg: String? = null
        var start = 0L
        var end = 0L
        for (i in intervals.filter { it.category in SESSION_CATEGORIES }.sortedBy { it.start }) {
            if (i.pkg == pkg && i.start - end <= SESSION_GAP_MS) {
                end = maxOf(end, i.end)
            } else {
                if (pkg != null) out += pkg to (end - start) / 60_000.0
                pkg = i.pkg
                start = i.start
                end = i.end
            }
        }
        if (pkg != null) out += pkg to (end - start) / 60_000.0
        return out
    }

    /** The session still running at [nowMillis] for [pkg], in minutes, or 0. */
    fun currentSession(intervals: List<Interval>, pkg: String, nowMillis: Long): Double {
        val mine = intervals.filter { it.pkg == pkg && it.category in SESSION_CATEGORIES }.sortedBy { it.start }
        if (mine.isEmpty() || nowMillis - mine.last().end > SESSION_GAP_MS) return 0.0
        var start = mine.last().start
        for (k in mine.size - 2 downTo 0) {
            if (start - mine[k].end <= SESSION_GAP_MS) start = mine[k].start else break
        }
        return (nowMillis - start) / 60_000.0
    }

    /**
     * What the child sees now, for the app in front.
     * @param bonus extra minutes the parent granted today.
     * @param breakUntil the end of a session break already running, if any.
     * @param bedtimeExtendedUntil the parent allowed more time during bedtime until then.
     */
    fun decide(
        policy: ScreenPolicy,
        now: LocalDateTime,
        nowMillis: Long,
        foreground: Interval?,
        totals: DayTotals,
        sessionMinutes: Double,
        bonus: Int,
        breakUntil: Long?,
        bedtimeExtendedUntil: Long? = null,
    ): Verdict {
        if (!policy.enabled || foreground == null) return Verdict.Allow
        val category = foreground.category
        val extended = bedtimeExtendedUntil != null && nowMillis < bedtimeExtendedUntil
        if (inBedtime(policy, now) && !extended) return Verdict.Block(BlockReason.BEDTIME, null)
        if (breakUntil != null && nowMillis < breakUntil && category in SESSION_CATEGORIES) {
            return Verdict.Block(BlockReason.SESSION, category, breakUntil)
        }
        dailyLimit(policy, now)?.let { limit ->
            if (totals.total >= limit + bonus) return Verdict.Block(BlockReason.DAILY, null)
        }
        policy.categoryLimits[category.wire]?.let { limit ->
            if (totals.minutes.getValue(category) >= limit + bonus) return Verdict.Block(BlockReason.CATEGORY, category)
        }
        if (policy.session.enabled && category in SESSION_CATEGORIES) {
            if (sessionMinutes >= policy.session.limitMinutes) {
                return Verdict.Block(BlockReason.SESSION, category, nowMillis + policy.session.breakMinutes * 60_000L)
            }
            if (sessionMinutes >= policy.session.nudgeMinutes) {
                return Verdict.Remind(RemindKind.SESSION, sessionMinutes.toInt())
            }
        }
        minutesToBedtime(policy, now)?.let { m ->
            if (policy.windDownMinutes > 0 && m in 1..policy.windDownMinutes) return Verdict.Remind(RemindKind.WIND_DOWN, m)
        }
        dailyLimit(policy, now)?.let { limit ->
            val left = limit + bonus - totals.total
            if (left in 1..10) return Verdict.Remind(RemindKind.TEN_MINUTES_LEFT, left)
        }
        return Verdict.Allow
    }

    private fun time(clock: String): LocalTime = LocalTime.parse(clock)

    private fun crossesMidnight(b: Bedtime) = time(b.end) <= time(b.start)

    private fun inWindow(b: Bedtime, t: LocalTime): Boolean {
        val start = time(b.start)
        val end = time(b.end)
        return if (end > start) t >= start && t < end else t >= start || t < end
    }

    private fun bedtimeMinutes(i: Interval, policy: ScreenPolicy, zone: java.time.ZoneId): Double {
        // Minute by minute is exact enough and simple across midnight.
        var count = 0.0
        var t = i.start
        while (t < i.end) {
            val step = minOf(60_000L, i.end - t)
            val local = LocalDateTime.ofInstant(java.time.Instant.ofEpochMilli(t), zone)
            if (inBedtime(policy, local)) count += step / 60_000.0
            t += step
        }
        return count
    }
}
