package com.rishikeshvk.unstuk.state

import android.app.NotificationManager
import android.media.AudioManager

/** A phone with nothing wrong: tests copy it and break the one setting they are about. */
val fineDeviceState = DeviceState(
    airplaneModeOn = false,
    keyguardLocked = false,
    interruptionFilter = NotificationManager.INTERRUPTION_FILTER_ALL,
    enabledAccessibilityServices = emptyList(),
    advancedProtectionOn = null,
    device = DeviceInfo("motorola", "moto edge 30", 34, "test"),
    ringerMode = AudioManager.RINGER_MODE_NORMAL,
    ringVolume = Volume(5, 7),
    callVolume = Volume(4, 5),
    wifiOn = true,
    mobileDataOn = true,
    online = true,
    dataSaverOn = false,
    autoTimeOn = true,
    privateDnsMode = "opportunistic",
    brightness = 128,
    screenTimeoutMs = 60_000,
    autoRotateOn = true,
    fontScale = 1.15f,
    inversionOn = false,
    greyscaleOn = false,
    bluetoothOn = true,
    bluetoothAudioConnected = false
)
