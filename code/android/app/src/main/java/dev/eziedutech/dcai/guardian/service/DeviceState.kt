package dev.eziedutech.dcai.guardian.service

import android.content.Context
import android.provider.Settings

/** The protection services this phone is actually running, for the heartbeat. */
object DeviceState {
    fun services(context: Context): Map<String, Boolean> = mapOf(
        // The persistent notification is shown the whole time the service runs.
        "notification" to true,
        "keyboard" to isKeyboardEnabled(context),
    )

    fun isKeyboardEnabled(context: Context): Boolean {
        val enabled = Settings.Secure.getString(
            context.contentResolver, Settings.Secure.ENABLED_INPUT_METHODS,
        ) ?: return false
        return enabled.split(":").any { it.startsWith(context.packageName) }
    }

    fun isKeyboardSelected(context: Context): Boolean {
        val current = Settings.Secure.getString(
            context.contentResolver, Settings.Secure.DEFAULT_INPUT_METHOD,
        ) ?: return false
        return current.startsWith(context.packageName)
    }
}
