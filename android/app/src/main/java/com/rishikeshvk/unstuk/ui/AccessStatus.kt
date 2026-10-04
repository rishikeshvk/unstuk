package com.rishikeshvk.unstuk.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.compose.LifecycleResumeEffect
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.rishikeshvk.unstuk.a11y.UnstukService
import com.rishikeshvk.unstuk.fix.Grant

/** Which of the accesses the rungs use are on. Each one missing only means more guided steps. */
data class AccessStatus(val service: Boolean, val policy: Boolean, val writeSettings: Boolean) {
    val complete: Boolean get() = service && policy && writeSettings
}

/** The current [AccessStatus], read again whenever the app comes back, since grants change in Settings. */
@Composable
fun rememberAccessStatus(): AccessStatus {
    val context = LocalContext.current
    val service by UnstukService.connected.collectAsStateWithLifecycle()
    var resumes by remember { mutableIntStateOf(0) }
    LifecycleResumeEffect(Unit) {
        resumes++
        onPauseOrDispose {}
    }
    return remember(service, resumes) {
        AccessStatus(
            service = service != null,
            policy = Grant.NOTIFICATION_POLICY.isGranted(context),
            writeSettings = Grant.WRITE_SETTINGS.isGranted(context)
        )
    }
}
