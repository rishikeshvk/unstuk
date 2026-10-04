package com.rishikeshvk.unstuk.action

import android.content.Context
import android.os.Build
import com.rishikeshvk.unstuk.selector.SelectorLoader
import com.rishikeshvk.unstuk.state.DeviceStateReader
import com.rishikeshvk.unstuk.trace.TraceEvent
import com.rishikeshvk.unstuk.trace.TraceWriter
import com.rishikeshvk.unstuk.trace.Tracer
import java.io.File
import kotlinx.coroutines.CancellationException

/** Runs one action under a trial id and always ends its trace with a `result` line. */
class ActionRunner(context: Context) {
    private val reader = DeviceStateReader(context)
    private val traces = TraceWriter(File(context.filesDir, "traces"))
    private val rung =
        AccessibilityRung(context, reader, SelectorLoader.load(context.assets, Build.MANUFACTURER))
    private val airplaneModeOff = AirplaneModeOff(reader, rung)
    private val dndOff = DndOff(context, reader, rung)

    suspend fun run(action: UnstukAction, trialId: String): ActionOutcome {
        val tracer = Tracer(traces, trialId, action.traceName)
        val outcome = try {
            when (action) {
                UnstukAction.AIRPLANE_MODE_OFF -> airplaneModeOff.run(tracer)
                UnstukAction.DND_OFF -> dndOff.run(tracer)
            }
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            // Node and system calls can throw when the UI changes under us; that run failed, the app goes on.
            ActionOutcome.Failed("${e::class.simpleName}: ${e.message}")
        }
        tracer.step("result", outcome.traceName, detail = outcome.reason())
        return outcome
    }

    fun trace(trialId: String): List<TraceEvent> = traces.read(trialId)

    private fun ActionOutcome.reason() = when (this) {
        is ActionOutcome.Failed -> reason
        is ActionOutcome.NeedsGuidance -> reason
        else -> null
    }
}
