package com.rishikeshvk.unstuk.fix

import android.app.NotificationManager
import android.content.Context
import android.provider.Settings

/** A special access the user grants in Settings. Without it, the direct rungs that need it are skipped. */
enum class Grant {
    NOTIFICATION_POLICY,
    WRITE_SETTINGS;

    fun isGranted(context: Context): Boolean = when (this) {
        NOTIFICATION_POLICY ->
            context.getSystemService(
                NotificationManager::class.java
            ).isNotificationPolicyAccessGranted
        WRITE_SETTINGS -> Settings.System.canWrite(context)
    }
}
