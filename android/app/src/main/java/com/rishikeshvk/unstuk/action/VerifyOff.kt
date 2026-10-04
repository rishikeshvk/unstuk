package com.rishikeshvk.unstuk.action

import com.rishikeshvk.unstuk.state.DeviceState
import com.rishikeshvk.unstuk.state.DeviceStateReader
import com.rishikeshvk.unstuk.trace.Tracer

/** The final word on success: whatever a rung reported, a fresh read must show the setting off. */
fun verifyOff(
    outcome: ActionOutcome,
    reader: DeviceStateReader,
    isOn: (DeviceState) -> Boolean,
    tracer: Tracer
): ActionOutcome {
    if (outcome != ActionOutcome.Verified) return outcome
    val off = !isOn(reader.read())
    tracer.step("verify", if (off) "off" else "still_on")
    return if (off) {
        ActionOutcome.Verified
    } else {
        ActionOutcome.Failed(
            "Fresh read still shows the setting on"
        )
    }
}
