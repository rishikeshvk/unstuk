package com.rishikeshvk.unstuk.flow

import com.rishikeshvk.unstuk.catalog.Catalog
import com.rishikeshvk.unstuk.decide.Execution
import com.rishikeshvk.unstuk.decide.IntentChoice
import com.rishikeshvk.unstuk.decide.RiskGate
import com.rishikeshvk.unstuk.diagnose.Diagnoser
import com.rishikeshvk.unstuk.state.DeviceState

private const val CLARIFY_CHOICES = 3

/** Turns a decision and a snapshot into a reply: decline, clarify, or diagnose and pass the fix through the gate. */
class Triage(private val catalog: Catalog, private val gate: RiskGate = RiskGate()) {
    private val diagnoser = Diagnoser(catalog)

    fun triage(choice: IntentChoice, state: DeviceState): Reply {
        val top = choice.top ?: return Reply.Decline(catalog.intents.map { it.option })
        if (gate.isTooUncertain(top.value)) {
            return Reply.Clarify(choice.leaders(CLARIFY_CHOICES).map(catalog::intent))
        }
        return forIntent(top.key, top.value, state)
    }

    fun forIntent(intentId: String, confidence: Double, state: DeviceState): Reply {
        val intent = catalog.intent(intentId)
        val fix = diagnoser.diagnose(intentId, state) ?: return Reply.AllClear(intent)
        return when (gate.execution(fix, confidence)) {
            Execution.GUIDED_ONLY -> Reply.Guide(fix, reason = null)
            Execution.CONFIRM -> Reply.Confirm(intent, fix, confidence)
            Execution.AUTOMATIC -> Reply.Run(intent, fix, confidence)
        }
    }

    /** After a verified fix: the next cause that still holds, offered rather than run. */
    fun next(intentId: String, confidence: Double, state: DeviceState): Reply? =
        when (val reply = forIntent(intentId, confidence, state)) {
            is Reply.Run -> Reply.Confirm(reply.intent, reply.fix, reply.confidence)
            is Reply.AllClear -> null
            else -> reply
        }
}
