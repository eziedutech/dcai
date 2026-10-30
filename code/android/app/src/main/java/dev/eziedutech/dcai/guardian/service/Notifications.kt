package dev.eziedutech.dcai.guardian.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.media.AudioAttributes
import android.media.RingtoneManager
import androidx.core.app.NotificationCompat
import dev.eziedutech.dcai.guardian.MainActivity
import dev.eziedutech.dcai.guardian.R
import dev.eziedutech.dcai.guardian.sites.SiteMatch
import dev.eziedutech.dcai.guardian.sites.SiteReviewActivity

/**
 * Two channels: a quiet, ongoing one that keeps "dcAI aktif" on screen the whole time the
 * service runs (the transparency requirement, and Google Play's rule for monitoring apps),
 * and a high-importance one for a nudge to the child.
 */
object Notifications {
    const val STATUS_CHANNEL = "dcai_status"
    // v2: a gentle chime and a soft vibration. A channel's sound is locked once created, so
    // a new id is needed for the change to take effect on phones that already had the old one.
    const val NUDGE_CHANNEL = "dcai_nudge2"
    const val STATUS_ID = 1
    private var nextNudgeId = 1000
    private const val SITE_ID_BASE = 5000

    fun ensureChannels(context: Context) {
        val manager = context.getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(
            NotificationChannel(STATUS_CHANNEL, context.getString(R.string.channel_status), NotificationManager.IMPORTANCE_LOW).apply {
                description = context.getString(R.string.channel_status_desc)
                setShowBadge(false)
            },
        )
        manager.deleteNotificationChannel("dcai_nudge") // replaced by the v2 channel below
        manager.createNotificationChannel(
            NotificationChannel(NUDGE_CHANNEL, context.getString(R.string.channel_nudge), NotificationManager.IMPORTANCE_HIGH).apply {
                description = context.getString(R.string.channel_nudge_desc)
                // Noticeable but gentle: a soft double-tap vibration and the default
                // notification chime, not an alarm; dcAI guides, it does not frighten.
                enableVibration(true)
                vibrationPattern = longArrayOf(0, 120, 80, 120)
                val attrs = AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_NOTIFICATION)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build()
                setSound(RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION), attrs)
            },
        )
    }

    private fun openApp(context: Context): PendingIntent {
        val intent = Intent(context, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
        return PendingIntent.getActivity(context, 0, intent, PendingIntent.FLAG_IMMUTABLE)
    }

    /** The persistent, non-dismissible notification shown the whole time dcAI runs. */
    fun statusNotification(context: Context, childNickname: String?): Notification {
        val text = if (childNickname != null) {
            context.getString(R.string.status_active_for, childNickname)
        } else {
            context.getString(R.string.status_active)
        }
        return NotificationCompat.Builder(context, STATUS_CHANNEL)
            .setSmallIcon(R.drawable.ic_shield)
            .setContentTitle(context.getString(R.string.app_name))
            .setContentText(text)
            .setOngoing(true)
            .setContentIntent(openApp(context))
            .setCategory(NotificationCompat.CATEGORY_STATUS)
            .build()
    }

    /** A site was held. The site's name stays on the phone: it is shown here and in review. */
    fun showSiteHeld(context: Context, match: SiteMatch) {
        val manager = context.getSystemService(NotificationManager::class.java)
        val text = context.getString(R.string.site_held_text, siteCategoryLabel(context, match.category))
        val review = Intent(context, SiteReviewActivity::class.java)
            .putExtra(SiteReviewActivity.EXTRA_SITE, match.listed)
            .putExtra(SiteReviewActivity.EXTRA_CATEGORY, match.category)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        val pending = PendingIntent.getActivity(
            context, match.listed.hashCode(), review, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
        val notification = NotificationCompat.Builder(context, NUDGE_CHANNEL)
            .setSmallIcon(R.drawable.ic_shield)
            .setContentTitle(context.getString(R.string.site_held_title))
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .setContentIntent(pending)
            .build()
        manager.notify(SITE_ID_BASE + (match.listed.hashCode() and 0xfff), notification)
    }

    fun siteCategoryLabel(context: Context, category: String): String = context.getString(
        when (category) {
            "dewasa" -> R.string.site_cat_dewasa
            "judi" -> R.string.site_cat_judi
            "penipuan" -> R.string.site_cat_penipuan
            "berbahaya" -> R.string.site_cat_berbahaya
            "kencan" -> R.string.site_cat_kencan
            "narkoba" -> R.string.site_cat_narkoba
            "kebencian" -> R.string.site_cat_kebencian
            else -> R.string.site_cat_lain
        },
    )

    private const val TIME_ID = 6000

    /** A gentle time reminder: winding down, a long session, ten minutes left. */
    fun showTimeReminder(context: Context, kind: dev.eziedutech.dcai.guardian.screen.RemindKind, minutes: Int) {
        val text = when (kind) {
            dev.eziedutech.dcai.guardian.screen.RemindKind.WIND_DOWN -> context.getString(R.string.time_remind_wind_down, minutes)
            dev.eziedutech.dcai.guardian.screen.RemindKind.SESSION -> context.getString(R.string.time_remind_session, minutes)
            dev.eziedutech.dcai.guardian.screen.RemindKind.TEN_MINUTES_LEFT -> context.getString(R.string.time_remind_left, minutes)
        }
        post(context, TIME_ID, context.getString(R.string.time_remind_title), text)
    }

    /** Used when dcAI may not open its break screen over other apps. */
    fun showTimeOut(context: Context, reason: dev.eziedutech.dcai.guardian.screen.BlockReason) {
        post(context, TIME_ID, context.getString(R.string.time_remind_title), context.getString(timeOutText(reason)))
    }

    fun showTimeDecision(context: Context, approved: Boolean, minutes: Int) {
        val text = if (approved) context.getString(R.string.time_decision_yes, minutes) else context.getString(R.string.time_decision_no)
        post(context, TIME_ID + 1, context.getString(R.string.time_decision_title), text)
    }

    fun timeOutText(reason: dev.eziedutech.dcai.guardian.screen.BlockReason): Int = when (reason) {
        dev.eziedutech.dcai.guardian.screen.BlockReason.BEDTIME -> R.string.timeout_bedtime_body
        dev.eziedutech.dcai.guardian.screen.BlockReason.DAILY -> R.string.timeout_daily_body
        dev.eziedutech.dcai.guardian.screen.BlockReason.CATEGORY -> R.string.timeout_category_body
        dev.eziedutech.dcai.guardian.screen.BlockReason.SESSION -> R.string.timeout_session_body
        dev.eziedutech.dcai.guardian.screen.BlockReason.APP_NOT_ALLOWED -> R.string.timeout_app_body
    }

    private fun post(context: Context, id: Int, title: String, text: String) {
        val manager = context.getSystemService(NotificationManager::class.java)
        manager.notify(
            id,
            NotificationCompat.Builder(context, NUDGE_CHANNEL)
                .setSmallIcon(R.drawable.ic_shield)
                .setContentTitle(title)
                .setContentText(text)
                .setStyle(NotificationCompat.BigTextStyle().bigText(text))
                .setAutoCancel(true)
                .setContentIntent(openApp(context))
                .build(),
        )
    }

    /** A friendly reminder for the child. */
    fun showNudge(context: Context, nudge: String) {
        val manager = context.getSystemService(NotificationManager::class.java)
        val notification = NotificationCompat.Builder(context, NUDGE_CHANNEL)
            .setSmallIcon(R.drawable.ic_shield)
            .setContentTitle(context.getString(R.string.nudge_title))
            .setContentText(nudge)
            .setStyle(NotificationCompat.BigTextStyle().bigText(nudge))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_SOCIAL)
            .setAutoCancel(true)
            .setContentIntent(openApp(context))
            .build()
        manager.notify(nextNudgeId++, notification)
    }
}
