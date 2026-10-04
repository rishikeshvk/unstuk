package com.rishikeshvk.unstuk.state

import android.annotation.SuppressLint
import android.app.KeyguardManager
import android.app.NotificationManager
import android.content.ContentResolver
import android.content.Context
import android.media.AudioDeviceInfo
import android.media.AudioManager
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.wifi.WifiManager
import android.os.Build
import android.provider.Settings
import android.security.advancedprotection.AdvancedProtectionManager
import android.telephony.TelephonyManager
import android.util.Log
import androidx.annotation.RequiresApi

private const val TAG = "DeviceStateReader"

// Not in the public SDK; readable only where the platform marks them @Readable (Android 12+).
private const val PRIVATE_DNS_MODE = "private_dns_mode"
private const val INVERSION_ENABLED = "accessibility_display_inversion_enabled"
private const val DALTONIZER_ENABLED = "accessibility_display_daltonizer_enabled"
private const val DALTONIZER_MODE = "accessibility_display_daltonizer"
private const val DALTONIZER_MONOCHROMACY = 0

// The BLE types are inlined constants; below API 31 no device reports them, so including them is harmless.
@SuppressLint("InlinedApi")
private val BLUETOOTH_OUTPUTS = setOf(
    AudioDeviceInfo.TYPE_BLUETOOTH_A2DP,
    AudioDeviceInfo.TYPE_BLUETOOTH_SCO,
    AudioDeviceInfo.TYPE_BLE_HEADSET,
    AudioDeviceInfo.TYPE_BLE_SPEAKER
)

/** Reads device state fresh on every call; nothing is cached, so a result can always be trusted as current. */
class DeviceStateReader(private val context: Context) {
    private val resolver: ContentResolver = context.contentResolver
    private val audio = context.getSystemService(AudioManager::class.java)
    private val connectivity = context.getSystemService(ConnectivityManager::class.java)

    fun read() = DeviceState(
        airplaneModeOn = Settings.Global.getInt(resolver, Settings.Global.AIRPLANE_MODE_ON, 0) == 1,
        keyguardLocked = context.getSystemService(KeyguardManager::class.java).isKeyguardLocked,
        interruptionFilter = context.getSystemService(
            NotificationManager::class.java
        ).currentInterruptionFilter,
        enabledAccessibilityServices = readEnabledAccessibilityServices(),
        advancedProtectionOn = if (Build.VERSION.SDK_INT >= 36) readAdvancedProtection() else null,
        device = DeviceInfo.current(),
        ringerMode = audio.ringerMode,
        ringVolume = volume(AudioManager.STREAM_RING),
        callVolume = volume(AudioManager.STREAM_VOICE_CALL),
        wifiOn = context.getSystemService(WifiManager::class.java).isWifiEnabled,
        mobileDataOn = readMobileData(),
        online = readOnline(),
        dataSaverOn = connectivity.restrictBackgroundStatus !=
            ConnectivityManager.RESTRICT_BACKGROUND_STATUS_DISABLED,
        autoTimeOn = Settings.Global.getInt(resolver, Settings.Global.AUTO_TIME, 1) == 1,
        privateDnsMode = readIfAllowed { Settings.Global.getString(resolver, PRIVATE_DNS_MODE) },
        brightness = Settings.System.getInt(resolver, Settings.System.SCREEN_BRIGHTNESS, 0),
        screenTimeoutMs = Settings.System.getInt(resolver, Settings.System.SCREEN_OFF_TIMEOUT, 0),
        autoRotateOn =
        Settings.System.getInt(resolver, Settings.System.ACCELEROMETER_ROTATION, 0) == 1,
        fontScale = Settings.System.getFloat(resolver, Settings.System.FONT_SCALE, 1f),
        inversionOn = readIfAllowed { Settings.Secure.getInt(resolver, INVERSION_ENABLED, 0) == 1 },
        greyscaleOn = readIfAllowed { readGreyscale() },
        bluetoothOn = Settings.Global.getInt(resolver, Settings.Global.BLUETOOTH_ON, 0) == 1,
        bluetoothAudioConnected = audio.getDevices(AudioManager.GET_DEVICES_OUTPUTS).any {
            it.type in BLUETOOTH_OUTPUTS
        }
    )

    private fun volume(stream: Int) =
        Volume(audio.getStreamVolume(stream), audio.getStreamMaxVolume(stream))

    private fun readEnabledAccessibilityServices(): List<String> {
        val raw = Settings.Secure.getString(
            resolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        )
        return raw.orEmpty().split(':').filter { it.isNotBlank() }
    }

    private fun readOnline(): Boolean {
        val network = connectivity.activeNetwork ?: return false
        val capabilities = connectivity.getNetworkCapabilities(network) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
    }

    // ACCESS_NETWORK_STATE is one of the accepted permissions, and readIfAllowed handles a refusal.
    @SuppressLint("MissingPermission")
    private fun readMobileData() = readIfAllowed {
        context.getSystemService(TelephonyManager::class.java).isDataEnabled
    }

    private fun readGreyscale() = Settings.Secure.getInt(resolver, DALTONIZER_ENABLED, 0) == 1 &&
        Settings.Secure.getInt(resolver, DALTONIZER_MODE, -1) == DALTONIZER_MONOCHROMACY

    @RequiresApi(36)
    private fun readAdvancedProtection() =
        context.getSystemService(AdvancedProtectionManager::class.java).isAdvancedProtectionEnabled

    // State the platform won't let us read is unknown, so the checks that need it simply don't fire.
    private fun <T> readIfAllowed(read: () -> T): T? = try {
        read()
    } catch (e: SecurityException) {
        Log.w(TAG, "Setting not readable", e)
        null
    }
}
