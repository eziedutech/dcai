package dev.eziedutech.dcai.guardian.data

import android.content.Context
import androidx.core.content.edit
import android.util.Base64
import dev.eziedutech.dcai.guardian.net.DeviceConfig
import dev.eziedutech.dcai.guardian.privacy.Pin
import dev.eziedutech.dcai.guardian.vision.Category
import dev.eziedutech.dcai.guardian.vision.ImageHash
import dev.eziedutech.dcai.guardian.vision.LocalTuning
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

    val hasPin: Boolean get() = prefs.contains(KEY_PIN_HASH)

    fun setPin(pin: String) {
        require(Pin.valid(pin))
        val salt = Pin.newSalt()
        prefs.edit {
            putString(KEY_PIN_SALT, b64(salt))
            putString(KEY_PIN_HASH, b64(Pin.hash(pin, salt)))
        }
    }

    fun checkPin(pin: String): Boolean {
        val salt = prefs.getString(KEY_PIN_SALT, null) ?: return false
        val hash = prefs.getString(KEY_PIN_HASH, null) ?: return false
        return Pin.matches(pin, unb64(salt), unb64(hash))
    }

    /** Images the parent confirmed as a false detection: perceptual hash and category. */
    fun confirmedFalse(): List<Pair<Long, Category>> =
        prefs.getStringSet(KEY_CONFIRMED, emptySet()).orEmpty().mapNotNull { entry ->
            val (hex, wire) = entry.split(':').takeIf { it.size == 2 } ?: return@mapNotNull null
            val category = Category.entries.firstOrNull { it.wire == wire } ?: return@mapNotNull null
            runCatching { ImageHash.fromHex(hex) to category }.getOrNull()
        }

    /** The phone's own threshold per sensitive category (tier 1). */
    fun thresholds(): Map<Category, Int> =
        Category.entries.mapNotNull { c -> prefs.getInt(KEY_THRESHOLD + c.wire, -1).takeIf { it >= 0 }?.let { c to it } }.toMap()

    fun recordFalseDetection(hash: Long, category: Category) {
        val entries = prefs.getStringSet(KEY_CONFIRMED, emptySet()).orEmpty().toMutableSet()
        entries += "${ImageHash.toHex(hash)}:${category.wire}"
        val raised = LocalTuning.raised(thresholds()[category], category)
        prefs.edit {
            // Capped so the list stays small on a phone.
            putStringSet(KEY_CONFIRMED, entries.toList().takeLast(MAX_CONFIRMED).toSet())
            putInt(KEY_THRESHOLD + category.wire, raised)
        }
    }

    /** Pairing ended (revoked by the parent, or the child's data was erased). The PIN and
     * the local image tuning go with it. */
    fun clear() = prefs.edit { clear() }

    private companion object {
        const val KEY_SERVER = "server_url"
        const val KEY_TOKEN = "device_token"
        const val KEY_CONFIG = "config"
        const val KEY_PIN_SALT = "pin_salt"
        const val KEY_PIN_HASH = "pin_hash"
        const val KEY_CONFIRMED = "vision_confirmed_false"
        const val KEY_THRESHOLD = "vision_threshold_"
        const val MAX_CONFIRMED = 200

        fun b64(bytes: ByteArray): String = Base64.encodeToString(bytes, Base64.NO_WRAP)
        fun unb64(text: String): ByteArray = Base64.decode(text, Base64.NO_WRAP)
    }
}
