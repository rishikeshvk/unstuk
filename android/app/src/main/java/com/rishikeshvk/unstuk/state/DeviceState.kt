package com.rishikeshvk.unstuk.state

import android.app.NotificationManager

private const val TALKBACK_PACKAGE = "com.google.android.marvin.talkback"

data class DeviceState(
    val airplaneModeOn: Boolean,
    val keyguardLocked: Boolean,
    val interruptionFilter: Int,
    val enabledAccessibilityServices: List<String>,
    /** Null below API 36, where Advanced Protection doesn't exist. */
    val advancedProtectionOn: Boolean?,
    val device: DeviceInfo
) {
    // PRIORITY, NONE and ALARMS all silence calls; UNKNOWN means the read failed, not that DND is off.
    val dndOn: Boolean get() = interruptionFilter > NotificationManager.INTERRUPTION_FILTER_ALL

    val talkBackOn: Boolean get() = enabledAccessibilityServices.any {
        it.startsWith("$TALKBACK_PACKAGE/")
    }
}
