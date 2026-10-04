package com.rishikeshvk.unstuk.diagnose

import android.media.AudioManager
import com.rishikeshvk.unstuk.state.DeviceState

// Below about 10% the screen is hard to read in daylight. Fixes use the same lines to judge success.
const val BRIGHTNESS_LOW = 26
const val TIMEOUT_SHORT_MS = 30_000

/** The causes the catalog can name, by check id. Each one reads only the snapshot it is given. */
object Checks {
    /** A cause that always applies, such as an explicit request; it is decided by the gate, not by state. */
    const val ALWAYS = "always"

    val all: Map<String, (DeviceState) -> Boolean> = mapOf(
        ALWAYS to { _ -> true },
        "airplane_on" to { s -> s.airplaneModeOn },
        "offline_mobile_data_off" to
            { s -> !s.online && !s.airplaneModeOn && s.mobileDataOn == false },
        "offline_wifi_off" to { s -> !s.online && !s.airplaneModeOn && !s.wifiOn },
        "data_saver_on" to { s -> s.dataSaverOn },
        "auto_time_off" to { s -> !s.autoTimeOn },
        "private_dns_hostname" to { s -> s.privateDnsMode == "hostname" },
        "dnd_on" to { s -> s.dndOn },
        "ringer_not_normal" to { s -> s.ringerMode != AudioManager.RINGER_MODE_NORMAL },
        "ring_volume_zero" to { s -> s.ringVolume.level == 0 },
        "call_volume_low" to { s -> s.callVolume.level * 2 < s.callVolume.max },
        "bluetooth_audio_connected" to { s -> s.bluetoothAudioConnected },
        "talkback_on" to { s -> s.talkBackOn },
        "inversion_on" to { s -> s.inversionOn == true },
        "greyscale_on" to { s -> s.greyscaleOn == true },
        "brightness_low" to { s -> s.brightness < BRIGHTNESS_LOW },
        "timeout_short" to { s -> s.screenTimeoutMs < TIMEOUT_SHORT_MS },
        "rotation_locked" to { s -> !s.autoRotateOn },
        "text_not_enlarged" to { s -> s.fontScale <= 1f },
        "bluetooth_off" to { s -> !s.bluetoothOn }
    )
}
