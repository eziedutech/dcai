package dev.eziedutech.dcai.guardian.service

import android.content.Context
import android.view.inputmethod.InputMethodManager

/** The protection services this phone is actually running, for the heartbeat. */
object DeviceState {
    fun services(context: Context): Map<String, Boolean> = mapOf(
        // The persistent notification is shown the whole time the service runs.
        "notification" to true,
        "keyboard" to isKeyboardEnabled(context),
        "vpn" to dev.eziedutech.dcai.guardian.sites.SiteGuardVpn.running,
    )

    /** Whether the dcAI keyboard is enabled. InputMethodManager needs no special read
     * permission, unlike Settings.Secure.ENABLED_INPUT_METHODS (blocked for targetSdk > 33). */
    fun isKeyboardEnabled(context: Context): Boolean {
        val imm = context.getSystemService(InputMethodManager::class.java) ?: return false
        return imm.enabledInputMethodList.any { it.packageName == context.packageName }
    }
}
