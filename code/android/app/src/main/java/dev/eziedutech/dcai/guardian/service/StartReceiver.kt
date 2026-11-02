package dev.eziedutech.dcai.guardian.service

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import dev.eziedutech.dcai.guardian.ServiceLocator

/**
 * Brings protection back after the phone restarts or dcAI is updated. Without it the service
 * (the "dcAI aktif" notification and the level stream) stayed off until the parent opened the
 * app, and images in an already risky chat went unchecked. Only a paired, set-up phone starts.
 * Both broadcasts may start a foreground service from the background.
 */
class StartReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Intent.ACTION_BOOT_COMPLETED && intent.action != Intent.ACTION_MY_PACKAGE_REPLACED) return
        val store = ServiceLocator.store(context)
        if (!store.isPaired || !store.setupDone) return
        runCatching { GuardianService.start(context) }
            .onFailure { Log.w(TAG, "start failed: ${it.javaClass.simpleName}") }
    }

    private companion object {
        const val TAG = "dcai.service"
    }
}
