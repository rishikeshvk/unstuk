package com.rishikeshvk.unstuk.fix

import android.app.NotificationManager
import android.content.Context
import android.media.AudioManager
import android.provider.Settings
import com.rishikeshvk.unstuk.diagnose.BRIGHTNESS_LOW
import com.rishikeshvk.unstuk.diagnose.TIMEOUT_SHORT_MS
import com.rishikeshvk.unstuk.selector.SettingTarget
import kotlin.math.ceil

// Not a public constant, but both targets' Settings export it; the public ZEN_MODE_PRIORITY_SETTINGS opens another page.
private const val ZEN_MODE_SETTINGS = "android.settings.ZEN_MODE_SETTINGS"

private const val BRIGHTNESS_HALF = 128
private const val TIMEOUT_ONE_MINUTE_MS = 60_000

/** The executor's half of the catalog: one [FixSpec] per fix id in `catalog/fixes.json`. */
object FixSpecs {
    val all: Map<String, FixSpec> = mapOf(
        "airplane_off" to FixSpec(
            reached = { _, s -> !s.airplaneModeOn },
            accessibility = SettingTarget.AIRPLANE_MODE,
            settingsAction = Settings.ACTION_AIRPLANE_MODE_SETTINGS
        ),
        // On Android 15+ setInterruptionFilter only changes the app's own zen rule, so it can't undo the user's DND.
        "dnd_off" to FixSpec(
            reached = { _, s -> !s.dndOn },
            direct = DirectChange(Grant.NOTIFICATION_POLICY, maxSdk = 34) {
                it.getSystemService(NotificationManager::class.java)
                    .setInterruptionFilter(NotificationManager.INTERRUPTION_FILTER_ALL)
            },
            accessibility = SettingTarget.DND,
            settingsAction = ZEN_MODE_SETTINGS
        ),
        "mobile_data_on" to FixSpec(
            reached = { _, s -> s.mobileDataOn == true },
            accessibility = SettingTarget.MOBILE_DATA,
            settingsAction = Settings.ACTION_DATA_ROAMING_SETTINGS
        ),
        "wifi_on" to FixSpec(
            reached = { _, s -> s.wifiOn },
            accessibility = SettingTarget.WIFI,
            settingsAction = Settings.ACTION_WIFI_SETTINGS
        ),
        "data_saver_off" to FixSpec(
            reached = { _, s -> !s.dataSaverOn },
            accessibility = SettingTarget.DATA_SAVER,
            settingsAction = Settings.ACTION_WIRELESS_SETTINGS
        ),
        "auto_time_on" to FixSpec(
            reached = { _, s -> s.autoTimeOn },
            accessibility = SettingTarget.AUTO_TIME,
            settingsAction = Settings.ACTION_DATE_SETTINGS
        ),
        // Null means unreadable, which must never count as fixed.
        "private_dns_off" to FixSpec(
            reached = { _, s -> s.privateDnsMode != null && s.privateDnsMode != "hostname" },
            panelAction = Settings.ACTION_WIRELESS_SETTINGS,
            settingsAction = Settings.ACTION_WIRELESS_SETTINGS
        ),
        "ringer_normal" to FixSpec(
            reached = { _, s -> s.ringerMode == AudioManager.RINGER_MODE_NORMAL },
            direct = DirectChange(grant = null) {
                it.audio().ringerMode = AudioManager.RINGER_MODE_NORMAL
            },
            settingsAction = Settings.ACTION_SOUND_SETTINGS
        ),
        "ring_volume_up" to FixSpec(
            reached = { _, s -> s.ringVolume.level > 0 },
            direct = DirectChange(grant = null) { it.setVolume(AudioManager.STREAM_RING, 0.7) },
            settingsAction = Settings.ACTION_SOUND_SETTINGS
        ),
        "call_volume_up" to FixSpec(
            reached = { _, s -> s.callVolume.level * 2 >= s.callVolume.max },
            direct = DirectChange(grant = null) {
                it.setVolume(AudioManager.STREAM_VOICE_CALL, 0.8)
            },
            settingsAction = Settings.ACTION_SOUND_SETTINGS
        ),
        "audio_output_switch" to FixSpec(reached = { _, s -> !s.bluetoothAudioConnected }),
        "talkback_off" to FixSpec(
            reached = { _, s -> !s.talkBackOn },
            accessibility = SettingTarget.TALKBACK,
            settingsAction = Settings.ACTION_ACCESSIBILITY_SETTINGS
        ),
        "inversion_off" to FixSpec(
            reached = { _, s -> s.inversionOn == false },
            accessibility = SettingTarget.INVERSION,
            settingsAction = Settings.ACTION_ACCESSIBILITY_SETTINGS
        ),
        "greyscale_off" to FixSpec(
            reached = { _, s -> s.greyscaleOn == false },
            settingsAction = Settings.ACTION_ACCESSIBILITY_SETTINGS
        ),
        "brightness_up" to FixSpec(
            reached = { _, s -> s.brightness >= BRIGHTNESS_LOW },
            direct = DirectChange(Grant.WRITE_SETTINGS) {
                it.putSystemInt(Settings.System.SCREEN_BRIGHTNESS, BRIGHTNESS_HALF)
            },
            settingsAction = Settings.ACTION_DISPLAY_SETTINGS
        ),
        "timeout_longer" to FixSpec(
            reached = { _, s -> s.screenTimeoutMs >= TIMEOUT_SHORT_MS },
            direct = DirectChange(Grant.WRITE_SETTINGS) {
                it.putSystemInt(Settings.System.SCREEN_OFF_TIMEOUT, TIMEOUT_ONE_MINUTE_MS)
            },
            settingsAction = Settings.ACTION_DISPLAY_SETTINGS
        ),
        "rotation_unlock" to FixSpec(
            reached = { _, s -> s.autoRotateOn },
            direct = DirectChange(Grant.WRITE_SETTINGS) {
                it.putSystemInt(Settings.System.ACCELEROMETER_ROTATION, 1)
            },
            accessibility = SettingTarget.AUTO_ROTATE,
            settingsAction = Settings.ACTION_DISPLAY_SETTINGS
        ),
        // The user picks the size, so any increase counts.
        "font_size_settings" to FixSpec(
            reached = { before, now -> now.fontScale > before.fontScale },
            panelAction = Settings.ACTION_DISPLAY_SETTINGS,
            settingsAction = Settings.ACTION_DISPLAY_SETTINGS
        ),
        "bluetooth_on" to FixSpec(
            reached = { _, s -> s.bluetoothOn },
            accessibility = SettingTarget.BLUETOOTH,
            settingsAction = Settings.ACTION_BLUETOOTH_SETTINGS
        ),
        // Destructive and guided only; nothing the app could read would prove the user did it.
        "reset_network" to FixSpec(reached = { _, _ -> false })
    )

    fun get(id: String): FixSpec = all.getValue(id)
}

private fun Context.audio() = getSystemService(AudioManager::class.java)

private fun Context.setVolume(stream: Int, fraction: Double) {
    val max = audio().getStreamMaxVolume(stream)
    audio().setStreamVolume(stream, ceil(max * fraction).toInt(), 0)
}

private fun Context.putSystemInt(key: String, value: Int) {
    Settings.System.putInt(contentResolver, key, value)
}
