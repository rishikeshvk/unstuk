package com.rishikeshvk.unstuk.decide

import com.rishikeshvk.unstuk.catalog.FixEntry
import com.rishikeshvk.unstuk.catalog.Risk
import com.rishikeshvk.unstuk.catalog.Rung

/** How a fix may run (AGENTS.md invariant 3). */
enum class Execution { AUTOMATIC, CONFIRM, GUIDED_ONLY }

/**
 * The risk gate. [autoThreshold] is a placeholder until M6 tunes it on calibrated probabilities; below
 * [clarifyBelow] the top intent is too uncertain to act on at all.
 */
class RiskGate(private val autoThreshold: Double = 0.8, private val clarifyBelow: Double = 0.5) {
    fun isTooUncertain(confidence: Double) = confidence < clarifyBelow

    fun execution(fix: FixEntry, confidence: Double): Execution = when {
        fix.risk == Risk.HIGH -> Execution.GUIDED_ONLY
        // Nothing to run, so asking "shall I?" would promise an action the app can't take.
        fix.rungs == listOf(Rung.GUIDED) -> Execution.GUIDED_ONLY
        fix.risk == Risk.MEDIUM -> Execution.CONFIRM
        confidence < autoThreshold -> Execution.CONFIRM
        else -> Execution.AUTOMATIC
    }
}
