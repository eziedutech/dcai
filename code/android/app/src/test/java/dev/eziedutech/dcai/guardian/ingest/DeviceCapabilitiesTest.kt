package dev.eziedutech.dcai.guardian.ingest

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The RAM gate that decides whether a phone is offered the on-device model. A 4 GB phone (and
 * any device the system flags low-RAM) must stay on the online path; only phones with clear
 * headroom pass. See docs/log/2026-11-02.md for why.
 */
class DeviceCapabilitiesTest {

    private val gib = 1024L * 1024 * 1024

    @Test
    fun fourGbPhoneIsNotOffered() {
        // A "4 GB" phone reports roughly 3.7 GiB of total RAM.
        assertFalse(DeviceCapabilities.supportsOnDevice((3.7 * gib).toLong(), isLowRamDevice = false))
    }

    @Test
    fun sixGbPhoneIsOffered() {
        // A "6 GB" phone reports roughly 5.6 GiB of total RAM.
        assertTrue(DeviceCapabilities.supportsOnDevice((5.6 * gib).toLong(), isLowRamDevice = false))
    }

    @Test
    fun eightGbPhoneIsOffered() {
        assertTrue(DeviceCapabilities.supportsOnDevice(8 * gib, isLowRamDevice = false))
    }

    @Test
    fun lowRamFlagAlwaysBlocksEvenWithEnoughBytes() {
        assertFalse(DeviceCapabilities.supportsOnDevice(8 * gib, isLowRamDevice = true))
    }

    @Test
    fun theThresholdBoundaryHolds() {
        assertFalse(DeviceCapabilities.supportsOnDevice(DeviceCapabilities.MIN_TOTAL_RAM_BYTES - 1, isLowRamDevice = false))
        assertTrue(DeviceCapabilities.supportsOnDevice(DeviceCapabilities.MIN_TOTAL_RAM_BYTES, isLowRamDevice = false))
    }
}
