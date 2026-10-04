package com.rishikeshvk.unstuk.state

import android.app.NotificationManager
import android.content.Context
import android.os.Build
import android.provider.Settings
import android.security.advancedprotection.AdvancedProtectionManager
import androidx.annotation.RequiresApi

/** Reads device state fresh on every call; nothing is cached, so a result can always be trusted as current. */
class DeviceStateReader(private val context: Context) {
    fun read() = DeviceState(
        airplaneModeOn =
        Settings.Global.getInt(context.contentResolver, Settings.Global.AIRPLANE_MODE_ON, 0) ==
            1,
        interruptionFilter = context.getSystemService(
            NotificationManager::class.java
        ).currentInterruptionFilter,
        enabledAccessibilityServices = readEnabledAccessibilityServices(),
        advancedProtectionOn = if (Build.VERSION.SDK_INT >= 36) readAdvancedProtection() else null,
        device = DeviceInfo.current()
    )

    private fun readEnabledAccessibilityServices(): List<String> {
        val raw = Settings.Secure.getString(
            context.contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        )
        return raw.orEmpty().split(':').filter { it.isNotBlank() }
    }

    @RequiresApi(36)
    private fun readAdvancedProtection() =
        context.getSystemService(AdvancedProtectionManager::class.java).isAdvancedProtectionEnabled
}
