package com.rishikeshvk.unstuk.state

import android.app.NotificationManager

private const val TALKBACK_PACKAGE = "com.google.android.marvin.talkback"

/** Null fields are settings this device or Android version doesn't let us read: unknown, never "off". */
data class DeviceState(
    val airplaneModeOn: Boolean,
    val keyguardLocked: Boolean,
    val interruptionFilter: Int,
    val enabledAccessibilityServices: List<String>,
    /** Null below API 36, where Advanced Protection doesn't exist. */
    val advancedProtectionOn: Boolean?,
    val device: DeviceInfo,
    val ringerMode: Int,
    val ringVolume: Volume,
    val callVolume: Volume,
    val wifiOn: Boolean,
    val mobileDataOn: Boolean?,
    /** An active network the system has validated as reaching the internet. */
    val online: Boolean,
    val dataSaverOn: Boolean,
    val autoTimeOn: Boolean,
    val privateDnsMode: String?,
    /** 0–255, the scale `Settings.System.SCREEN_BRIGHTNESS` uses. */
    val brightness: Int,
    val screenTimeoutMs: Int,
    val autoRotateOn: Boolean,
    val fontScale: Float,
    val inversionOn: Boolean?,
    val greyscaleOn: Boolean?,
    val bluetoothOn: Boolean,
    val bluetoothAudioConnected: Boolean
) {
    // PRIORITY, NONE and ALARMS all silence calls; UNKNOWN means the read failed, not that DND is off.
    val dndOn: Boolean get() = interruptionFilter > NotificationManager.INTERRUPTION_FILTER_ALL

    val talkBackOn: Boolean get() = enabledAccessibilityServices.any {
        it.startsWith("$TALKBACK_PACKAGE/")
    }
}
