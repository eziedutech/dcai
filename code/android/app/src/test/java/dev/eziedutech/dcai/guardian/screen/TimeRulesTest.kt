package dev.eziedutech.dcai.guardian.screen

import dev.eziedutech.dcai.guardian.net.Bedtime
import dev.eziedutech.dcai.guardian.net.ScreenPolicy
import dev.eziedutech.dcai.guardian.net.SessionRule
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalDateTime
import java.time.ZoneOffset

class TimeRulesTest {
    private val zone = ZoneOffset.UTC
    private val policy = ScreenPolicy(
        dailyLimitSchool = 120,
        dailyLimitWeekend = 180,
        categoryLimits = mapOf("video" to 60, "game" to 45, "sosial" to null, "lain" to null),
        bedtimeSchool = Bedtime(start = "21:00", end = "05:30"),
        bedtimeWeekend = Bedtime(start = "22:00", end = "06:30"),
        windDownMinutes = 15,
        session = SessionRule(nudgeMinutes = 20, limitMinutes = 40, breakMinutes = 5),
    )

    // 2026-10-28 is a Wednesday (school day); 2026-10-31 a Saturday.
    private val wed = LocalDateTime.of(2026, 10, 28, 16, 0)
    private fun ms(t: LocalDateTime) = t.toInstant(zone).toEpochMilli()
    private fun iv(pkg: String, cat: AppCategory, from: LocalDateTime, minutes: Long) =
        Interval(pkg, cat, ms(from), ms(from.plusMinutes(minutes)))

    private fun totals(vararg m: Pair<AppCategory, Int>) =
        DayTotals(AppCategory.entries.associateWith { c -> m.firstOrNull { it.first == c }?.second ?: 0 }, 0, 0)

    private fun decide(now: LocalDateTime, fg: Interval?, t: DayTotals, session: Double = 0.0, bonus: Int = 0, breakUntil: Long? = null) =
        TimeRules.decide(policy, now, ms(now), fg, t, session, bonus, breakUntil)

    @Test
    fun bedtimeCrossesMidnightAndBelongsToTheEvening() {
        assertTrue(TimeRules.inBedtime(policy, LocalDateTime.of(2026, 10, 28, 21, 30)))
        assertTrue(TimeRules.inBedtime(policy, LocalDateTime.of(2026, 10, 29, 5, 0)))
        assertFalse(TimeRules.inBedtime(policy, LocalDateTime.of(2026, 10, 29, 5, 45)))
        // Friday night follows Friday's school-day bedtime; Saturday night the weekend one.
        assertTrue(TimeRules.inBedtime(policy, LocalDateTime.of(2026, 10, 30, 21, 30)))
        assertFalse(TimeRules.inBedtime(policy, LocalDateTime.of(2026, 10, 31, 21, 30)))
        assertTrue(TimeRules.inBedtime(policy, LocalDateTime.of(2026, 11, 1, 6, 0)))
    }

    @Test
    fun minutesToBedtime() {
        assertEquals(10, TimeRules.minutesToBedtime(policy, LocalDateTime.of(2026, 10, 28, 20, 50)))
        assertEquals(0, TimeRules.minutesToBedtime(policy, LocalDateTime.of(2026, 10, 28, 22, 0)))
    }

    @Test
    fun totalsAddUpPerCategoryAndCountBedtime() {
        val night = LocalDateTime.of(2026, 10, 28, 20, 50)
        val t = TimeRules.totals(listOf(iv("v", AppCategory.VIDEO, night, 20), iv("g", AppCategory.GAME, wed, 30)), policy, zone)
        assertEquals(20, t.minutes[AppCategory.VIDEO])
        assertEquals(30, t.minutes[AppCategory.GAME])
        assertEquals(10, t.bedtimeMinutes)
    }

    @Test
    fun sessionJoinsShortGapsAndSplitsLongOnes() {
        val a = iv("v", AppCategory.VIDEO, wed, 10)
        val b = iv("v", AppCategory.VIDEO, wed.plusMinutes(11), 10)
        val c = iv("v", AppCategory.VIDEO, wed.plusMinutes(30), 5)
        val s = TimeRules.sessions(listOf(a, b, c))
        assertEquals(2, s.size)
        assertEquals(21.0, s[0].second, 0.01)
        assertEquals(21.0, TimeRules.currentSession(listOf(a, b), "v", ms(wed.plusMinutes(21))), 0.01)
        assertEquals(0.0, TimeRules.currentSession(listOf(a), "v", ms(wed.plusMinutes(20))), 0.01)
    }

    @Test
    fun bedtimeBlocksEverything() {
        val night = LocalDateTime.of(2026, 10, 28, 22, 0)
        val v = decide(night, iv("g", AppCategory.GAME, night, 1), totals())
        assertEquals(Verdict.Block(BlockReason.BEDTIME, null), v)
    }

    @Test
    fun dailyAndCategoryLimitsWithBonus() {
        val fg = iv("g", AppCategory.GAME, wed, 1)
        assertEquals(BlockReason.DAILY, (decide(wed, fg, totals(AppCategory.LAIN to 120)) as Verdict.Block).reason)
        assertEquals(Verdict.Allow, decide(wed, fg, totals(AppCategory.LAIN to 100), bonus = 30))
        assertEquals(BlockReason.CATEGORY, (decide(wed, fg, totals(AppCategory.GAME to 45)) as Verdict.Block).reason)
        // No limit for sosial.
        assertEquals(Verdict.Allow, decide(wed, iv("s", AppCategory.SOSIAL, wed, 1), totals(AppCategory.SOSIAL to 70)))
    }

    @Test
    fun sessionNudgesThenBreaks() {
        val fg = iv("v", AppCategory.VIDEO, wed, 1)
        assertEquals(Verdict.Remind(RemindKind.SESSION, 25), decide(wed, fg, totals(), session = 25.0))
        val block = decide(wed, fg, totals(), session = 41.0) as Verdict.Block
        assertEquals(BlockReason.SESSION, block.reason)
        assertEquals(ms(wed) + 5 * 60_000L, block.untilMillis)
        // During the break another short-video app is held too; a game is not.
        assertTrue(decide(wed, iv("s", AppCategory.SOSIAL, wed, 1), totals(), breakUntil = block.untilMillis) is Verdict.Block)
        assertEquals(Verdict.Allow, decide(wed, iv("g", AppCategory.GAME, wed, 1), totals(), breakUntil = block.untilMillis))
    }

    @Test
    fun windDownAndTenMinutesLeft() {
        val evening = LocalDateTime.of(2026, 10, 28, 20, 50)
        assertEquals(Verdict.Remind(RemindKind.WIND_DOWN, 10), decide(evening, iv("g", AppCategory.GAME, evening, 1), totals()))
        assertEquals(Verdict.Remind(RemindKind.TEN_MINUTES_LEFT, 5), decide(wed, iv("l", AppCategory.LAIN, wed, 1), totals(AppCategory.LAIN to 115)))
    }

    @Test
    fun disabledPolicyOrNoAppAllows() {
        assertEquals(Verdict.Allow, TimeRules.decide(policy.copy(enabled = false), wed, ms(wed), iv("g", AppCategory.GAME, wed, 1), totals(AppCategory.GAME to 500), 0.0, 0, null))
        assertEquals(Verdict.Allow, decide(wed, null, totals(AppCategory.GAME to 500)))
        assertNull(TimeRules.bedtimeAt(policy.copy(bedtimeSchool = Bedtime(enabled = false)), LocalDateTime.of(2026, 10, 28, 22, 0)))
    }
}
