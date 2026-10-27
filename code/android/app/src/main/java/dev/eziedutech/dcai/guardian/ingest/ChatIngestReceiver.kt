package dev.eziedutech.dcai.guardian.ingest

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import dev.eziedutech.dcai.guardian.ServiceLocator
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

/**
 * How an app that integrated dcAI (here, the sample chat app) hands a message to dcAI
 * Guardian. The broadcast is explicit and guarded by a signature-level permission, so only
 * an app signed with the same key can send it. The raw text is masked inside submit()
 * before anything leaves the phone.
 */
class ChatIngestReceiver : BroadcastReceiver() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != ACTION) return
        val text = intent.getStringExtra(EXTRA_TEXT)?.takeIf { it.isNotBlank() } ?: return
        val ingest = ServiceLocator.ingest(context.applicationContext) ?: return
        val pending = goAsync()
        scope.launch {
            try {
                ingest.submit(
                    threadId = intent.getStringExtra(EXTRA_THREAD) ?: "default",
                    appPackage = intent.getStringExtra(EXTRA_APP) ?: "unknown.app",
                    channel = intent.getStringExtra(EXTRA_CHANNEL) ?: "dm",
                    contactKnown = intent.getBooleanExtra(EXTRA_CONTACT_KNOWN, false),
                    sender = intent.getStringExtra(EXTRA_SENDER) ?: "contact",
                    rawText = text,
                    contactName = intent.getStringExtra(EXTRA_CONTACT_NAME),
                )
            } finally {
                pending.finish()
            }
        }
    }

    companion object {
        const val ACTION = "dev.eziedutech.dcai.guardian.INGEST_MESSAGE"
        const val EXTRA_THREAD = "thread"
        const val EXTRA_APP = "app"
        const val EXTRA_CHANNEL = "channel"
        const val EXTRA_SENDER = "sender"
        const val EXTRA_TEXT = "text"
        const val EXTRA_CONTACT_NAME = "contact_name"
        const val EXTRA_CONTACT_KNOWN = "contact_known"
    }
}
