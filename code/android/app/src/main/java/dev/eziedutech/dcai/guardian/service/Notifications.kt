package dev.eziedutech.dcai.guardian.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import dev.eziedutech.dcai.guardian.MainActivity
import dev.eziedutech.dcai.guardian.R

/**
 * Two channels: a quiet, ongoing one that keeps "dcAI aktif" on screen the whole time the
 * service runs (the transparency requirement, and Google Play's rule for monitoring apps),
 * and a high-importance one for a nudge to the child.
 */
object Notifications {
    const val STATUS_CHANNEL = "dcai_status"
    const val NUDGE_CHANNEL = "dcai_nudge"
    const val STATUS_ID = 1
    private var nextNudgeId = 1000

    fun ensureChannels(context: Context) {
        val manager = context.getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(
            NotificationChannel(STATUS_CHANNEL, context.getString(R.string.channel_status), NotificationManager.IMPORTANCE_LOW).apply {
                description = context.getString(R.string.channel_status_desc)
                setShowBadge(false)
            },
        )
        manager.createNotificationChannel(
            NotificationChannel(NUDGE_CHANNEL, context.getString(R.string.channel_nudge), NotificationManager.IMPORTANCE_HIGH).apply {
                description = context.getString(R.string.channel_nudge_desc)
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
