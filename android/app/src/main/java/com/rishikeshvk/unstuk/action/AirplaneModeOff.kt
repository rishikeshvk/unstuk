package com.rishikeshvk.unstuk.action

import android.content.Intent
import android.provider.Settings
import com.rishikeshvk.unstuk.selector.SettingTarget
import com.rishikeshvk.unstuk.state.DeviceStateReader
import com.rishikeshvk.unstuk.trace.Tracer

/** Airplane mode has no direct API for third-party apps, so this goes straight to the accessibility rung. */
class AirplaneModeOff(private val reader: DeviceStateReader, private val rung: AccessibilityRung) {
    suspend fun run(tracer: Tracer): ActionOutcome {
        val before = reader.read()
        tracer.step("precondition", if (before.airplaneModeOn) "on" else "off")
        if (!before.airplaneModeOn) return ActionOutcome.NothingToDo
        if (before.keyguardLocked) return ActionOutcome.NeedsUnlock

        val outcome = rung.switchOff(
            SettingTarget.AIRPLANE_MODE,
            Intent(Settings.ACTION_AIRPLANE_MODE_SETTINGS),
            isOn = { it.airplaneModeOn },
            tracer = tracer
        )
        return verifyOff(outcome, reader, { it.airplaneModeOn }, tracer)
    }
}
