package com.rishikeshvk.unstuk.action

import android.content.Context
import android.os.Build
import com.rishikeshvk.unstuk.fix.DirectChange
import com.rishikeshvk.unstuk.state.DeviceState
import com.rishikeshvk.unstuk.state.DeviceStateReader
import com.rishikeshvk.unstuk.state.awaitState
import com.rishikeshvk.unstuk.trace.Tracer
import kotlin.time.Duration.Companion.seconds

private val STATE_TIMEOUT = 5.seconds

/** Makes the change through a system API. A missing grant or a refusal hands over to the next rung. */
class DirectRung(private val context: Context, private val reader: DeviceStateReader) {
    suspend fun apply(
        change: DirectChange,
        reached: (DeviceState) -> Boolean,
        tracer: Tracer
    ): ActionOutcome {
        if (Build.VERSION.SDK_INT > change.maxSdk) {
            return ActionOutcome.NeedsGuidance("Direct API unavailable above API ${change.maxSdk}")
        }
        val grant = change.grant
        if (grant != null && !grant.isGranted(context)) {
            return ActionOutcome.NeedsGuidance("${grant.name} not granted")
        }
        try {
            change.apply(context)
        } catch (e: SecurityException) {
            return ActionOutcome.NeedsGuidance("Direct API refused: ${e.message}")
        }
        tracer.step("direct_api", "called")
        val changed = awaitState(context, reader, STATE_TIMEOUT, reached)
        tracer.step("wait_state", if (changed != null) "changed" else "timeout")
        return if (changed !=
            null
        ) {
            ActionOutcome.Verified
        } else {
            ActionOutcome.Failed("State did not change in time")
        }
    }
}
