package dev.eziedutech.dcai.guardian.net

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * Wire shapes for the device API (code/backpy/app/api/devices.py). Field names match the
 * backend. Unknown fields are ignored by the Json parser, so the backend can add fields
 * without breaking the app.
 */
@Serializable
data class PairRequest(
    val code: String,
    @SerialName("device_name") val deviceName: String,
    val platform: String = "android",
    @SerialName("app_version") val appVersion: String,
)

@Serializable
data class PairResponse(
    @SerialName("device_id") val deviceId: String,
    @SerialName("device_token") val deviceToken: String,
    val config: DeviceConfig,
)

@Serializable
data class DeviceConfig(
    @SerialName("device_id") val deviceId: String,
    @SerialName("child_nickname") val childNickname: String,
    @SerialName("age_range") val ageRange: String,
    val language: String,
    val scopes: List<String>,
    @SerialName("consent_version") val consentVersion: String? = null,
    @SerialName("stream_path") val streamPath: String = "/v1/device/stream",
) {
    fun has(scope: String) = scope in scopes
}

@Serializable
data class HeartbeatRequest(
    @SerialName("app_version") val appVersion: String,
    val services: Map<String, Boolean>,
)

@Serializable
data class DeviceMessageRequest(
    @SerialName("thread_key") val threadKey: String,
    val app: String,
    val channel: String,
    @SerialName("contact_known") val contactKnown: Boolean,
    val sender: String,
    val text: String,
    @SerialName("contact_name") val contactName: String? = null,
)

@Serializable
data class DeviceNudge(
    val situation: String,
    @SerialName("child_nudge") val childNudge: String,
    @SerialName("help_channels") val helpChannels: List<String> = emptyList(),
)

@Serializable
data class DeviceMessageResponse(
    @SerialName("conversation_id") val conversationId: String,
    val queued: Boolean,
    @SerialName("message_index") val messageIndex: Int? = null,
    val level: String? = null,
    val raised: Boolean? = null,
    val nudge: DeviceNudge? = null,
)

@Serializable
data class ImageSignalRequest(
    @SerialName("thread_key") val threadKey: String? = null,
    val trigger: String,
    val sender: String? = null,
    val category: String,
    val action: String,
    val score: Int,
    @SerialName("model_version") val modelVersion: String,
)

@Serializable
data class SiteListEntry(val name: String, val count: Int, val bytes: Long, val sha256: String)

@Serializable
data class SiteManifest(
    val version: String,
    val source: String,
    val license: String,
    val categories: List<SiteListEntry>,
)

/** A site held on the phone: the category only. There is no field for the site's name. */
@Serializable
data class SiteSignalRequest(
    val category: String,
    @SerialName("list_version") val listVersion: String,
)

/** A false detection the parent confirmed on the child's phone, without the image. */
@Serializable
data class DetectionFeedbackRequest(
    /** gambar or domain. */
    val kind: String = "gambar",
    val category: String,
    val score: Int,
    @SerialName("model_version") val modelVersion: String,
    val verdict: String = "salah_deteksi",
    @SerialName("confirmed_by_guardian") val confirmedByGuardian: Boolean = true,
)

/** A live update on the device stream: event name plus already-parsed JSON object. */
data class LiveEvent(val event: String, val data: kotlinx.serialization.json.JsonObject)
