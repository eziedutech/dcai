package dev.eziedutech.dcai.guardian.data

import android.content.Context
import androidx.core.content.edit
import dev.eziedutech.dcai.guardian.net.DeviceConfig
import kotlinx.serialization.json.Json

/**
 * What the phone remembers between runs: the server URL, the device token and the last
 * configuration. The device token is a bearer credential; a shipping build should move it
 * to the Android Keystore. For the hackathon prototype it lives in private app storage,
 * which is sandboxed per app.
 */
class GuardianStore(context: Context) {
    private val prefs = context.getSharedPreferences("dcai_guardian", Context.MODE_PRIVATE)
    private val json = Json { ignoreUnknownKeys = true }

    var serverUrl: String?
        get() = prefs.getString(KEY_SERVER, null)
        set(value) = prefs.edit { putString(KEY_SERVER, value) }

    var deviceToken: String?
        get() = prefs.getString(KEY_TOKEN, null)
        set(value) = prefs.edit { putString(KEY_TOKEN, value) }

    var config: DeviceConfig?
        get() = prefs.getString(KEY_CONFIG, null)?.let {
            runCatching { json.decodeFromString<DeviceConfig>(it) }.getOrNull()
        }
        set(value) = prefs.edit {
            if (value == null) remove(KEY_CONFIG)
            else putString(KEY_CONFIG, json.encodeToString(value))
        }

    val isPaired: Boolean get() = deviceToken != null && serverUrl != null

    /** Pairing ended (revoked by the parent, or the child's data was erased). */
    fun clear() = prefs.edit { clear() }

    private companion object {
        const val KEY_SERVER = "server_url"
        const val KEY_TOKEN = "device_token"
        const val KEY_CONFIG = "config"
    }
}
