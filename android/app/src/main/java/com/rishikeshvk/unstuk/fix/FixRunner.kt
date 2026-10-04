package com.rishikeshvk.unstuk.fix

import android.content.Context
import android.content.Intent
import android.os.Build
import com.rishikeshvk.unstuk.action.AccessibilityRung
import com.rishikeshvk.unstuk.action.ActionOutcome
import com.rishikeshvk.unstuk.action.DirectRung
import com.rishikeshvk.unstuk.action.PanelRung
import com.rishikeshvk.unstuk.catalog.FixEntry
import com.rishikeshvk.unstuk.catalog.Rung
import com.rishikeshvk.unstuk.selector.SelectorLoader
import com.rishikeshvk.unstuk.state.DeviceState
import com.rishikeshvk.unstuk.state.DeviceStateReader
import com.rishikeshvk.unstuk.trace.Tracer
import kotlinx.coroutines.CancellationException

/**
 * Walks a fix's rungs in catalog order. A rung that can't act or fails hands over to the next; guided steps end
 * the ladder. Only a fresh read after the last rung can turn an outcome into [ActionOutcome.Verified].
 */
class FixRunner(private val context: Context) {
    private val reader = DeviceStateReader(context)
    private val direct = DirectRung(context, reader)
    private val panel = PanelRung(context, reader)
    private val accessibility =
        AccessibilityRung(context, reader, SelectorLoader.load(context.assets, Build.MANUFACTURER))

    suspend fun run(fix: FixEntry, tracer: Tracer): ActionOutcome = try {
        climb(fix, FixSpecs.get(fix.id), tracer)
    } catch (e: CancellationException) {
        throw e
    } catch (e: Exception) {
        // Node and system calls can throw when the UI changes under us; that run failed, the app goes on.
        ActionOutcome.Failed("${e::class.simpleName}: ${e.message}")
    }

    private suspend fun climb(fix: FixEntry, spec: FixSpec, tracer: Tracer): ActionOutcome {
        val before = reader.read()
        val reached: (DeviceState) -> Boolean = { spec.reached(before, it) }
        val alreadyReached = reached(before)
        tracer.step("precondition", if (alreadyReached) "reached" else "needs_change")
        if (alreadyReached) return ActionOutcome.NothingToDo

        var last: ActionOutcome = ActionOutcome.NeedsGuidance("No automated rung")
        for (rung in fix.rungs) {
            if (rung.needsUnlockedScreen() &&
                reader.read().keyguardLocked
            ) {
                return ActionOutcome.NeedsUnlock
            }
            val outcome = when (rung) {
                Rung.GUIDED -> break
                Rung.DIRECT -> direct.apply(checkNotNull(spec.direct), reached, tracer)
                Rung.PANEL -> panel.open(checkNotNull(spec.panelAction), reached, tracer)
                Rung.ACCESSIBILITY -> accessibility.toggle(
                    checkNotNull(spec.accessibility),
                    spec.settingsAction?.let(::Intent),
                    reached,
                    tracer
                )
            }
            tracer.step("rung_${rung.name.lowercase()}", outcome.traceName, detail = outcome.reason)
            if (outcome == ActionOutcome.Verified) return verify(reached, tracer)
            last = outcome
        }
        return last
    }

    // The final word on success: whatever a rung reported, a fresh read must agree.
    private fun verify(reached: (DeviceState) -> Boolean, tracer: Tracer): ActionOutcome {
        val ok = reached(reader.read())
        tracer.step("verify", if (ok) "reached" else "not_reached")
        return if (ok) {
            ActionOutcome.Verified
        } else {
            ActionOutcome.Failed(
                "Fresh read disagrees with the rung"
            )
        }
    }
}

private fun Rung.needsUnlockedScreen() = this == Rung.PANEL || this == Rung.ACCESSIBILITY
