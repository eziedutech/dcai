package dev.eziedutech.dcai.guardian.screen

import android.content.Context
import android.content.Intent
import android.provider.Settings
import android.util.Log
import dev.eziedutech.dcai.guardian.ServiceLocator
import dev.eziedutech.dcai.guardian.net.ScreenPolicy
import dev.eziedutech.dcai.guardian.net.UsageDayRequest
import dev.eziedutech.dcai.guardian.net.UsageRequest
import dev.eziedutech.dcai.guardian.service.Notifications
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.ZoneId

/** What the home screen shows about today, refreshed by each check. */
data class TodayState(
    val usedMinutes: Int,
    val limitMinutes: Int?,
    val bonusMinutes: Int,
    val bedtimeStart: String?,
    val inBedtime: Boolean,
) {
    val leftMinutes: Int? get() = limitMinutes?.let { maxOf(0, it + bonusMinutes - usedMinutes) }
}

/**
 * Time online on the phone. Every couple of seconds while dcAI runs: read app use since
 * midnight, decide with [TimeRules], show a reminder or the break screen, and send the day's
 * totals now and then. Nothing here reads inside an app.
 */
class ScreenGuard(private val context: Context) {
    private val reader = UsageReader(context)
    private val zone: ZoneId get() = ZoneId.systemDefault()
    private var breakUntil: Long? = null
    private var sessionFloor = 0L
    private val lastRemind = HashMap<RemindKind, Long>()
    private var lastUpload = 0L
    private var uploadedDay: LocalDate? = null

    fun canRead() = reader.hasPermission()

    fun canShowOverScreen() = Settings.canDrawOverlays(context)

    suspend fun tick() {
        val store = ServiceLocator.store(context)
        val config = store.config ?: return
        val policy = config.screenPolicy
        if (!config.has("waktu") || policy == null || !reader.hasPermission()) {
            today = null
            return
        }
        val nowMs = System.currentTimeMillis()
        val now = LocalDateTime.now(zone)
        val day = now.toLocalDate()
        val midnight = day.atStartOfDay(zone).toInstant().toEpochMilli()
        val allowed = policy.alwaysAllowed.toSet()
        val intervals = reader.intervals(midnight, nowMs, allowed)
        val totals = TimeRules.totals(intervals, policy, zone)
        val bonus = store.bonusMinutes(day)
        today = TodayState(
            usedMinutes = totals.total,
            limitMinutes = TimeRules.dailyLimit(policy, now),
            bonusMinutes = bonus,
            bedtimeStart = (if (TimeRules.isSchoolDay(policy, now.dayOfWeek)) policy.bedtimeSchool else policy.bedtimeWeekend)
                .takeIf { it.enabled }?.start,
            inBedtime = TimeRules.inBedtime(policy, now),
        )

        val fg = reader.foreground(intervals, nowMs)
        // After a break, the next session starts from zero.
        breakUntil?.let { if (nowMs >= it) { sessionFloor = it; breakUntil = null } }
        val session = fg?.let { f ->
            TimeRules.currentSession(intervals.filter { it.end > sessionFloor }.map { it.copy(start = maxOf(it.start, sessionFloor)) }, f.pkg, nowMs)
        } ?: 0.0

        val extended = store.bedtimeExtendedUntil.takeIf { it > 0 }
        when (val v = TimeRules.decide(policy, now, nowMs, fg, totals, session, bonus, breakUntil, extended)) {
            is Verdict.Block -> {
                if (v.reason == BlockReason.SESSION && breakUntil == null) {
                    breakUntil = v.untilMillis
                    store.addSessionLimit(day)
                }
                showBreak(v)
            }
            is Verdict.Remind -> remind(v, nowMs)
            Verdict.Allow -> Unit
        }
        upload(policy, totals, day, nowMs)
    }

    /** The parent said yes: the minutes count today, a running break ends, and at bedtime
     * the minutes extend it. */
    fun onApproved(minutes: Int) {
        val store = ServiceLocator.store(context)
        val now = LocalDateTime.now(zone)
        val nowMs = System.currentTimeMillis()
        store.addBonus(now.toLocalDate(), minutes)
        breakUntil = null
        sessionFloor = nowMs
        val policy = store.config?.screenPolicy
        if (policy != null && TimeRules.inBedtime(policy, now)) store.bedtimeExtendedUntil = nowMs + minutes * 60_000L
    }

    private fun showBreak(v: Verdict.Block) {
        if (TimeOutActivity.visible) return
        val intent = Intent(context, TimeOutActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_NO_ANIMATION)
            .putExtra(TimeOutActivity.EXTRA_REASON, v.reason.name)
            .putExtra(TimeOutActivity.EXTRA_CATEGORY, v.category?.wire)
            .putExtra(TimeOutActivity.EXTRA_UNTIL, v.untilMillis ?: 0L)
        // Opening over another app needs "display over other apps"; without it, a notification.
        if (canShowOverScreen()) runCatching { context.startActivity(intent) } else Notifications.showTimeOut(context, v.reason)
    }

    private fun remind(v: Verdict.Remind, nowMs: Long) {
        if (nowMs - (lastRemind[v.kind] ?: 0L) < REMIND_EVERY_MS) return
        lastRemind[v.kind] = nowMs
        Notifications.showTimeReminder(context, v.kind, v.minutes)
    }

    private suspend fun upload(policy: ScreenPolicy, totals: DayTotals, day: LocalDate, nowMs: Long) {
        if (nowMs - lastUpload < UPLOAD_EVERY_MS && uploadedDay == day) return
        val client = ServiceLocator.client(context) ?: return
        val store = ServiceLocator.store(context)
        val days = mutableListOf(dayRequest(day, totals, store.sessionLimits(day)))
        // The first send after midnight closes yesterday with its full totals.
        if (uploadedDay != null && uploadedDay != day) {
            val y = day.minusDays(1)
            val from = y.atStartOfDay(zone).toInstant().toEpochMilli()
            val to = day.atStartOfDay(zone).toInstant().toEpochMilli()
            val yTotals = TimeRules.totals(reader.intervals(from, to, policy.alwaysAllowed.toSet()), policy, zone)
            days.add(0, dayRequest(y, yTotals, store.sessionLimits(y)))
        }
        runCatching { client.sendUsage(UsageRequest(days)) }
            .onSuccess {
                lastUpload = nowMs
                uploadedDay = day
            }
            .onFailure { Log.d(TAG, "usage upload failed: ${it.javaClass.simpleName}") }
    }

    private fun dayRequest(day: LocalDate, t: DayTotals, limits: Int) = UsageDayRequest(
        day = day.toString(),
        minutes = t.minutes.mapKeys { it.key.wire },
        bedtimeMinutes = t.bedtimeMinutes,
        longestSession = t.longestSession,
        sessionLimits = limits,
    )

    companion object {
        private const val TAG = "dcai.screen"
        private const val REMIND_EVERY_MS = 10 * 60_000L
        private const val UPLOAD_EVERY_MS = 10 * 60_000L

        /** Bumped on each decision from the parent, so an open break screen can close. */
        val decisions = kotlinx.coroutines.flow.MutableStateFlow(0)

        /** The latest check, for the home screen. Null when time online is off. */
        @Volatile var today: TodayState? = null
            private set
    }
}
