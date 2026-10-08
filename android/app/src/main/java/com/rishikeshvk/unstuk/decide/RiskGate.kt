package com.rishikeshvk.unstuk.decide

import com.rishikeshvk.unstuk.catalog.FixEntry
import com.rishikeshvk.unstuk.catalog.GateLines
import com.rishikeshvk.unstuk.catalog.Risk
import com.rishikeshvk.unstuk.catalog.Rung

/** How a fix may run (AGENTS.md invariant 3). */
enum class Execution { AUTOMATIC, CONFIRM, GUIDED_ONLY }

/** The risk gate, on [lines] tuned on dev against the model's calibrated probabilities (M6). */
class RiskGate(private val lines: GateLines) {
    /** Too unsure to act on: the top intent is low, or a second one is nearly as likely. */
    fun isTooUncertain(choice: IntentChoice): Boolean {
        // A lone intent's runner-up is 0.
        val (top, runnerUp) = choice.leaders(2).map(choice.probabilities::getValue) + 0.0
        return top < lines.clarifyBelow || top - runnerUp < lines.clarifyMargin
    }

    fun execution(fix: FixEntry, confidence: Double): Execution = when {
        fix.risk == Risk.HIGH -> Execution.GUIDED_ONLY
        // Nothing to run, so asking "shall I?" would promise an action the app can't take.
        fix.rungs == listOf(Rung.GUIDED) -> Execution.GUIDED_ONLY
        fix.risk == Risk.MEDIUM -> Execution.CONFIRM
        confidence < lines.automaticAt -> Execution.CONFIRM
        else -> Execution.AUTOMATIC
    }
}
