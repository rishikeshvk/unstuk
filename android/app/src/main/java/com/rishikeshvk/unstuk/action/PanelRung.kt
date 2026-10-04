package com.rishikeshvk.unstuk.action

import android.content.Context
import android.content.Intent
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.ProcessLifecycleOwner
import androidx.lifecycle.eventFlow
import com.rishikeshvk.unstuk.state.DeviceState
import com.rishikeshvk.unstuk.state.DeviceStateReader
import com.rishikeshvk.unstuk.state.awaitState
import com.rishikeshvk.unstuk.trace.Tracer
import kotlin.time.Duration.Companion.minutes
import kotlinx.coroutines.flow.dropWhile
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.merge
import kotlinx.coroutines.withTimeoutOrNull

private val PANEL_TIMEOUT = 2.minutes

/**
 * Opens a Settings screen for the user to tap, then waits until the setting changes or the user comes back to
 * Unstuk. Either way a fresh read decides; a user who came back without changing it gets guided steps.
 */
class PanelRung(private val context: Context, private val reader: DeviceStateReader) {
    suspend fun open(
        action: String,
        reached: (DeviceState) -> Boolean,
        tracer: Tracer
    ): ActionOutcome {
        context.startActivity(Intent(action).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        tracer.step("open_panel", "started", detail = action)
        val ended = withTimeoutOrNull(PANEL_TIMEOUT) {
            merge(
                flow {
                    awaitState(context, reader, PANEL_TIMEOUT, reached)?.let { emit("changed") }
                },
                flow {
                    userReturned()
                    emit("user_returned")
                }
            ).first()
        }
        tracer.step("wait_panel", ended ?: "timeout")
        return if (reached(reader.read())) {
            ActionOutcome.Verified
        } else {
            ActionOutcome.NeedsGuidance("Setting unchanged after the panel")
        }
    }

    // The process lifecycle reports ON_PAUSE about 700 ms after our last activity pauses, so subscribing after
    // startActivity still sees it.
    private suspend fun userReturned() {
        ProcessLifecycleOwner.get().lifecycle.eventFlow
            .dropWhile { it != Lifecycle.Event.ON_PAUSE }
            .first { it == Lifecycle.Event.ON_RESUME }
    }
}
