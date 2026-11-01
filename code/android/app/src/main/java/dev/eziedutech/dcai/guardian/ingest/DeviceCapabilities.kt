package dev.eziedutech.dcai.guardian.ingest

import android.app.ActivityManager
import android.content.Context

/**
 * Whether this phone has enough memory to run the on-device stage 1 model safely.
 *
 * The model needs about 1.2 GB resident while it runs. On a 4 GB phone that margin is too thin:
 * under real foreground load the OEM memory manager can reclaim dcAI's own process, which both
 * drops protection briefly and turns the accessibility scope off (measured on a 3.8 GB device,
 * see docs/log/2026-11-02.md). So on-device is only offered on phones with clear headroom;
 * smaller phones stay on the online path, which is the default anyway.
 */
object DeviceCapabilities {
    // A phone reports less total RAM than its nominal size: the kernel and reserved regions are
    // not counted, so a "6 GB" phone reports roughly 5.5 GiB and a "4 GB" phone under 4 GiB.
    // Requiring 5 GiB of reported total cleanly admits 6 GB-class phones and excludes 4 GB ones.
    const val MIN_TOTAL_RAM_BYTES = 5L * 1024 * 1024 * 1024

    /** The pure decision, so it is unit tested without a device. */
    fun supportsOnDevice(totalMemBytes: Long, isLowRamDevice: Boolean): Boolean =
        !isLowRamDevice && totalMemBytes >= MIN_TOTAL_RAM_BYTES

    /** Reads this device's total RAM and low-RAM flag and applies [supportsOnDevice]. */
    fun supportsOnDevice(context: Context): Boolean {
        val am = context.getSystemService(Context.ACTIVITY_SERVICE) as? ActivityManager
            ?: return false
        val mem = ActivityManager.MemoryInfo().also { am.getMemoryInfo(it) }
        return supportsOnDevice(mem.totalMem, am.isLowRamDevice)
    }
}
