package dev.eziedutech.dcai.guardian.ingest

import android.util.Base64
import dev.eziedutech.dcai.guardian.data.AnalysisMode
import dev.eziedutech.dcai.guardian.data.GuardianStore
import dev.eziedutech.dcai.guardian.net.BackendClient
import dev.eziedutech.dcai.guardian.net.DeviceMessageRequest
import dev.eziedutech.dcai.guardian.net.DeviceMessageResponse
import dev.eziedutech.dcai.guardian.privacy.Mask
import java.security.MessageDigest

// On-device send policy: a message is sent when it carries any label or a signal at or above
// this low threshold. Generous on purpose, since the on-device model is less sensitive than
// the server; its high precision keeps this from flooding the server with ordinary chat.
private const val ONDEVICE_SEND_SIGNAL = 20

/**
 * One path from a message seen on the phone to the backend. Both ingest sources, the
 * sample chat app and the dcAI keyboard, call this, so masking happens the same way for
 * both.
 *
 * The raw text is masked here, on the phone. Only the masked text leaves. The chat's
 * title never leaves either: the thread key is a hash made on the phone.
 */
class MessageIngest(
    private val store: GuardianStore,
    private val client: BackendClient,
    private val analyzer: OnDeviceAnalyzer = NoOnDeviceAnalyzer,
) {
    /**
     * @param threadId a stable identifier of the conversation on the phone (chat title,
     *   room id). It is hashed here and never sent in the clear.
     * @param appPackage the package name of the app the chat is in.
     * @param sender "child" or "contact".
     * @param rawText the message as typed or shown.
     * @param contactName the other person's display name, masked out before sending.
     */
    suspend fun submit(
        threadId: String,
        appPackage: String,
        channel: String,
        contactKnown: Boolean,
        sender: String,
        rawText: String,
        contactName: String? = null,
        wait: Boolean = false,
    ): DeviceMessageResponse? {
        if (store.config?.has("percakapan") != true) return null
        val knownNames = listOfNotNull(store.config?.childNickname, contactName).filter { it.isNotBlank() }
        // The backend takes up to 1000 characters; text from an image can be longer.
        val maskedText = Mask.mask(rawText, knownNames).text.take(1000)
        if (maskedText.isBlank()) return null

        // On-device mode: judge the masked message on the phone and send only the flagged
        // ones. Online mode (the default) always sends the masked text for the server to
        // judge. If the parent chose on-device but no model is installed, or the model
        // declines, fall through and send (fail safe).
        if (store.analysisMode == AnalysisMode.ONDEVICE && analyzer.installed) {
            val r = analyzer.label(sender, maskedText)
            val flagged = r == null || r.labels.isNotEmpty() || r.signal >= ONDEVICE_SEND_SIGNAL
            if (!flagged) return null
        }

        val request = DeviceMessageRequest(
            threadKey = threadKey(appPackage, threadId),
            app = appPackage,
            channel = channel,
            contactKnown = contactKnown,
            sender = sender,
            text = maskedText,
            // The contact name is masked inside the text; it is not sent as a field.
            contactName = null,
        )
        return client.sendMessage(request, wait = wait)
    }
}

/** The conversation's key as the server sees it: a hash made on the phone, never the title. */
fun threadKey(appPackage: String, threadId: String): String {
    val digest = MessageDigest.getInstance("SHA-256").digest("$appPackage:$threadId".toByteArray())
    // URL-safe base64, no padding: matches the backend's [A-Za-z0-9_-]{16,64} rule.
    return Base64.encodeToString(digest, Base64.URL_SAFE or Base64.NO_PADDING or Base64.NO_WRAP).take(43)
}
