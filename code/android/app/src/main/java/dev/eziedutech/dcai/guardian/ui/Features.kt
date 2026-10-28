package dev.eziedutech.dcai.guardian.ui

import android.content.Context
import androidx.annotation.StringRes
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Forum
import androidx.compose.material.icons.rounded.Image
import androidx.compose.material.icons.rounded.Keyboard
import androidx.compose.material.icons.rounded.Language
import androidx.compose.material.icons.rounded.Mic
import androidx.compose.material.icons.rounded.Timer
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.core.app.NotificationManagerCompat
import dev.eziedutech.dcai.guardian.R
import dev.eziedutech.dcai.guardian.ServiceLocator
import dev.eziedutech.dcai.guardian.net.DeviceConfig
import dev.eziedutech.dcai.guardian.screen.ScreenGuard
import dev.eziedutech.dcai.guardian.screen.TodayState
import dev.eziedutech.dcai.guardian.screen.UsageReader
import dev.eziedutech.dcai.guardian.service.DeviceState
import dev.eziedutech.dcai.guardian.sites.SiteGuardVpn
import dev.eziedutech.dcai.guardian.ui.art.Art

/** What dcAI helps with, one per consent scope, with the copy shown on its detail page. */
enum class Feature(
    val scope: String,
    val icon: ImageVector,
    val art: Art,
    @StringRes val title: Int,
    @StringRes val short: Int,
    @StringRes val what: Int,
    @StringRes val stays: Int,
    @StringRes val sent: Int,
) {
    OBROLAN("percakapan", Icons.Rounded.Forum, Art.CHAT, R.string.f_chat, R.string.f_chat_short, R.string.f_chat_what, R.string.f_chat_stays, R.string.f_chat_sent),
    GAMBAR("gambar", Icons.Rounded.Image, Art.IMAGE, R.string.f_image, R.string.f_image_short, R.string.f_image_what, R.string.f_image_stays, R.string.f_image_sent),
    SITUS("domain", Icons.Rounded.Language, Art.SITE, R.string.f_site, R.string.f_site_short, R.string.f_site_what, R.string.f_site_stays, R.string.f_site_sent),
    SUARA("suara", Icons.Rounded.Mic, Art.VOICE, R.string.f_voice, R.string.f_voice_short, R.string.f_voice_what, R.string.f_voice_stays, R.string.f_voice_sent),
    PAPAN_KETIK("keyboard", Icons.Rounded.Keyboard, Art.KEYBOARD, R.string.f_keyboard, R.string.f_keyboard_short, R.string.f_keyboard_what, R.string.f_keyboard_stays, R.string.f_keyboard_sent),
    WAKTU("waktu", Icons.Rounded.Timer, Art.CLOCK, R.string.f_time, R.string.f_time_short, R.string.f_time_what, R.string.f_time_stays, R.string.f_time_sent),
}

/** The phone's protection state at one moment, read again whenever the app comes back. */
data class Snapshot(
    val config: DeviceConfig?,
    val notificationsOn: Boolean,
    val keyboardOn: Boolean,
    val sitesOn: Boolean,
    val sensitiveModel: Boolean,
    val usageOn: Boolean = false,
    val overlayOn: Boolean = false,
    val today: TodayState? = null,
) {
    fun granted(f: Feature) = config?.has(f.scope) == true

    fun status(f: Feature): Status = when {
        !granted(f) -> Status.NOT_GRANTED
        f == Feature.SITUS -> if (sitesOn) Status.ON else Status.NEEDS_SETUP
        f == Feature.PAPAN_KETIK -> if (keyboardOn) Status.ON else Status.NEEDS_SETUP
        f == Feature.WAKTU -> if (usageOn && overlayOn) Status.ON else Status.NEEDS_SETUP
        // Voice notes are assessed by the backend; recording them on this phone comes later.
        f == Feature.SUARA -> Status.SOON
        else -> Status.ON
    }

    /** Things the child's phone should switch on but has not. */
    val issues: Int
        get() = (if (notificationsOn) 0 else 1) + Feature.entries.count { status(it) == Status.NEEDS_SETUP }

    companion object {
        fun read(context: Context) = Snapshot(
            config = ServiceLocator.store(context).config,
            notificationsOn = NotificationManagerCompat.from(context).areNotificationsEnabled(),
            keyboardOn = DeviceState.isKeyboardEnabled(context),
            sitesOn = SiteGuardVpn.running,
            sensitiveModel = ServiceLocator.sensitiveModel.installed,
            usageOn = UsageReader(context).hasPermission(),
            overlayOn = android.provider.Settings.canDrawOverlays(context),
            today = ScreenGuard.today,
        )
    }
}
