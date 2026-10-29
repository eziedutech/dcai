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
    @SerialName("screen_policy") val screenPolicy: ScreenPolicy? = null,
) {
    fun has(scope: String) = scope in scopes
}

/** The parent's time online settings (code/backpy/app/family/policy.py). */
@Serializable
data class Bedtime(val enabled: Boolean = true, val start: String = "21:00", val end: String = "05:30")

@Serializable
data class SessionRule(
    val enabled: Boolean = true,
    @SerialName("nudge_minutes") val nudgeMinutes: Int = 20,
    @SerialName("limit_minutes") val limitMinutes: Int = 40,
    @SerialName("break_minutes") val breakMinutes: Int = 5,
)

@Serializable
data class ScreenPolicy(
    val enabled: Boolean = true,
    @SerialName("school_days") val schoolDays: List<Int> = listOf(1, 2, 3, 4, 5),
    @SerialName("daily_limit_school") val dailyLimitSchool: Int? = 150,
    @SerialName("daily_limit_weekend") val dailyLimitWeekend: Int? = 210,
    @SerialName("category_limits") val categoryLimits: Map<String, Int?> = emptyMap(),
    @SerialName("bedtime_school") val bedtimeSchool: Bedtime = Bedtime(),
    @SerialName("bedtime_weekend") val bedtimeWeekend: Bedtime = Bedtime(start = "22:00", end = "06:30"),
    @SerialName("wind_down_minutes") val windDownMinutes: Int = 15,
    val session: SessionRule = SessionRule(),
    @SerialName("always_allowed") val alwaysAllowed: List<String> = emptyList(),
)

@Serializable
data class UsageDayRequest(
    val day: String,
    val minutes: Map<String, Int>,
    @SerialName("bedtime_minutes") val bedtimeMinutes: Int,
    @SerialName("longest_session") val longestSession: Int,
    @SerialName("session_limits") val sessionLimits: Int,
)

@Serializable
data class UsageRequest(val days: List<UsageDayRequest>)

@Serializable
data class TimeRequestContext(
    @SerialName("used_today") val usedToday: Int,
    @SerialName("limit_today") val limitToday: Int? = null,
    val category: String? = null,
    @SerialName("minutes_to_bedtime") val minutesToBedtime: Int? = null,
)

@Serializable
data class TimeRequestBody(val minutes: Int, val reason: String, val context: TimeRequestContext)

@Serializable
data class TimeRequestOut(
    val id: String,
    val minutes: Int,
    val status: String,
    @SerialName("granted_minutes") val grantedMinutes: Int = 0,
)

@Serializable
data class ConsentText(val version: String, val id: String, val en: String, val scopes: List<String>)

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
data class LiveEvent(val event: String, val data: kotlinx.serialization.json.JsonObject, val id: String? = null)
