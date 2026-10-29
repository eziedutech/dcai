package dev.eziedutech.dcai.guardian.ingest

import android.app.Notification
import android.content.ComponentName
import android.content.Context
import android.provider.Settings
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import androidx.core.app.NotificationCompat
import dev.eziedutech.dcai.guardian.ServiceLocator
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import java.util.concurrent.ConcurrentHashMap

/**
 * Incoming messages, read from the notifications of chat apps on the child's phone, so the
 * other person's side of a chat is assessed too. Android asks for this access in its own
 * settings screen; the parent turns it on at setup and the child sees dcAI in that list.
 *
 * Only message notifications are read (MessagingStyle or the message category), only while
 * the parent consents to chats, and the text goes through the same masking as every other
 * message before anything leaves the phone. Nothing is stored on the phone.
 */
class MessageNotificationListener : NotificationListenerService() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        if (sbn.packageName == packageName) return
        val ingest = ServiceLocator.ingest(applicationContext) ?: return
        val messages = IncomingMessages.read(sbn.notification) ?: return
        for (m in messages) {
            if (!Seen.first(sbn.packageName, m)) continue
            RecentThreads.note(sbn.packageName, m.threadId)
            scope.launch {
                runCatching {
                    ingest.submit(
                        threadId = m.threadId,
                        appPackage = sbn.packageName,
                        channel = if (m.group) "group" else "dm",
                        contactKnown = m.contactKnown,
                        sender = if (m.fromChild) "child" else "contact",
                        rawText = m.text,
                        contactName = m.senderName,
                    )
                }
            }
        }
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    companion object {
        /** Whether the parent turned on notification access for dcAI. */
        fun enabled(context: Context): Boolean {
            val flat = Settings.Secure.getString(context.contentResolver, "enabled_notification_listeners") ?: return false
            val me = ComponentName(context, MessageNotificationListener::class.java)
            return flat.split(":").any { ComponentName.unflattenFromString(it) == me }
        }
    }
}

/** One message as a chat app's notification shows it. */
data class IncomingMessage(
    val threadId: String,
    val senderName: String?,
    val text: String,
    val time: Long,
    val group: Boolean,
    val fromChild: Boolean,
    val contactKnown: Boolean,
)

object IncomingMessages {
    // A sender shown as a number is not in the child's contacts.
    private val PHONE_LIKE = Regex("""^[+\d][\d\s()\-]{6,}$""")

    /** The messages in a chat notification, or null for any other notification. */
    fun read(n: Notification): List<IncomingMessage>? {
        if (n.flags and Notification.FLAG_GROUP_SUMMARY != 0) return null
        val style = NotificationCompat.MessagingStyle.extractMessagingStyleFromNotification(n)
        if (style != null) {
            val title = style.conversationTitle?.toString()
            val group = style.isGroupConversation
            return style.messages.mapNotNull { m ->
                val text = m.text?.toString()?.trim().orEmpty()
                if (text.isEmpty()) return@mapNotNull null
                val name = m.person?.name?.toString()
                // A message without a person, or from the notification's own user, is the child's.
                val fromChild = m.person == null || name == style.user.name?.toString()
                val thread = title ?: name ?: return@mapNotNull null
                IncomingMessage(thread, name, text, m.timestamp, group, fromChild, contactKnown(name))
            }
        }
        if (n.category != Notification.CATEGORY_MESSAGE) return null
        val extras = n.extras ?: return null
        val name = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString() ?: return null
        val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString()?.trim().orEmpty()
        if (text.isEmpty()) return null
        return listOf(IncomingMessage(name, name, text, n.`when`, false, false, contactKnown(name)))
    }

    fun contactKnown(name: String?): Boolean = name != null && !PHONE_LIKE.matches(name.trim())
}

/** Chat notifications repeat earlier messages as new ones arrive; each is sent once. */
object Seen {
    private val keys = ConcurrentHashMap<String, Long>()
    private const val KEEP = 2000

    fun first(pkg: String, m: IncomingMessage): Boolean {
        val key = "$pkg|${m.threadId}|${m.time}|${m.text.hashCode()}"
        if (keys.putIfAbsent(key, m.time) != null) return false
        if (keys.size > KEEP) keys.entries.sortedBy { it.value }.take(KEEP / 2).forEach { keys.remove(it.key) }
        return true
    }
}

/**
 * The chat last seen in each app's notifications, so what the child types back with the
 * dcAI keyboard joins the same conversation as the messages it answers.
 */
object RecentThreads {
    private const val WINDOW_MS = 10 * 60 * 1000L
    private val last = ConcurrentHashMap<String, Pair<String, Long>>()

    fun note(pkg: String, threadId: String, now: Long = System.currentTimeMillis()) {
        last[pkg] = threadId to now
    }

    fun current(pkg: String, now: Long = System.currentTimeMillis()): String? =
        last[pkg]?.takeIf { now - it.second <= WINDOW_MS }?.first
}
