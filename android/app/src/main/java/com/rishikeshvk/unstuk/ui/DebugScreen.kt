package com.rishikeshvk.unstuk.ui

import android.app.NotificationManager
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.LifecycleResumeEffect
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.rishikeshvk.unstuk.a11y.UnstukService
import com.rishikeshvk.unstuk.state.DeviceState
import com.rishikeshvk.unstuk.state.DeviceStateReader

@Composable
fun DebugScreen(reader: DeviceStateReader, modifier: Modifier = Modifier) {
    var state by remember { mutableStateOf(reader.read()) }
    val service by UnstukService.connected.collectAsStateWithLifecycle()
    // Settings changed elsewhere (the shade, adb) are picked up when the screen comes back.
    LifecycleResumeEffect(reader) {
        state = reader.read()
        onPauseOrDispose {}
    }
    Column(
        modifier = modifier
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text("Device state", style = MaterialTheme.typography.titleLarge)
        StateRow("Unstuk service", if (service != null) "connected" else "not connected")
        DeviceStateTable(state)
        Button(onClick = { state = reader.read() }) { Text("Refresh") }
    }
}

@Composable
private fun DeviceStateTable(state: DeviceState) {
    StateRow("Airplane mode", onOff(state.airplaneModeOn))
    StateRow("Do Not Disturb", "${onOff(state.dndOn)} (${filterName(state.interruptionFilter)})")
    StateRow("TalkBack", onOff(state.talkBackOn))
    StateRow("Advanced Protection", state.advancedProtectionOn?.let(::onOff) ?: "n/a")
    StateRow(
        "Accessibility services",
        state.enabledAccessibilityServices.joinToString("\n").ifEmpty {
            "none"
        }
    )
    StateRow("Device", "${state.device.make} ${state.device.model}")
    StateRow("SDK", state.device.sdk.toString())
    StateRow("Build", state.device.build)
}

@Composable
private fun StateRow(label: String, value: String) {
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(label, modifier = Modifier.weight(0.4f), style = MaterialTheme.typography.labelLarge)
        Text(value, modifier = Modifier.weight(0.6f), style = MaterialTheme.typography.bodyMedium)
    }
}

private fun onOff(on: Boolean) = if (on) "on" else "off"

private fun filterName(filter: Int) = when (filter) {
    NotificationManager.INTERRUPTION_FILTER_ALL -> "all"
    NotificationManager.INTERRUPTION_FILTER_PRIORITY -> "priority"
    NotificationManager.INTERRUPTION_FILTER_NONE -> "none"
    NotificationManager.INTERRUPTION_FILTER_ALARMS -> "alarms"
    else -> "unknown"
}
