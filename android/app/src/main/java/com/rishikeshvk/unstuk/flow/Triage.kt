package com.rishikeshvk.unstuk.flow

import com.rishikeshvk.unstuk.action.ActionOutcome
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
        val top = choice.top ?: return Reply.Decline
        if (gate.isTooUncertain(top.value)) {
            return Reply.Clarify(choice.leaders(CLARIFY_CHOICES).map(catalog::intent))
        }
        return forIntent(top.key, top.value, state)
    }

    fun forIntent(intentId: String, confidence: Double, state: DeviceState): Reply {
        val intent = catalog.intent(intentId)
        val scan = diagnoser.scan(intentId, state)
        val fix = diagnoser.diagnose(intentId, state) ?: return Reply.AllClear(intent, scan)
        return when (gate.execution(fix, confidence)) {
            Execution.GUIDED_ONLY -> Reply.Guide(intent, fix, reason = null, scan = scan)
            Execution.CONFIRM -> Reply.Confirm(intent, fix, confidence, scan)
            Execution.AUTOMATIC -> Reply.Run(intent, fix, confidence, scan)
        }
    }

    /** After a verified fix: the next cause that still holds, offered rather than run. */
    fun next(intentId: String, confidence: Double, state: DeviceState): Reply? =
        when (val reply = forIntent(intentId, confidence, state)) {
            is Reply.Run -> Reply.Confirm(reply.intent, reply.fix, reply.confidence, reply.scan)
            is Reply.AllClear -> null
            else -> reply
        }

    /** The reply to a finished run, from the snapshot read right after it. */
    fun afterRun(
        outcome: ActionOutcome,
        intentId: String,
        fixId: String,
        confidence: Double,
        state: DeviceState
    ): Reply {
        val intent = catalog.intent(intentId)
        val fix = catalog.fix(fixId)
        return when (outcome) {
            ActionOutcome.Verified -> fixed(intentId, fixId, confidence, state)
            ActionOutcome.NothingToDo -> Reply.AlreadyFine(intent, fix)
            ActionOutcome.NeedsUnlock -> Reply.NeedsUnlock
            is ActionOutcome.NeedsGuidance, is ActionOutcome.Failed ->
                Reply.Guide(intent, fix, outcome.reason, diagnoser.scan(intentId, state))
        }
    }

    /** The user followed a guide and asks for a check: only a fresh snapshot without the cause counts as fixed. */
    fun recheck(intentId: String, fixId: String, confidence: Double, state: DeviceState): Reply {
        val scan = diagnoser.scan(intentId, state)
        val stillFound = scan.first { it.fix.id == fixId }.holds
        if (!stillFound) return fixed(intentId, fixId, confidence, state)
        return Reply.Guide(
            catalog.intent(intentId),
            catalog.fix(fixId),
            reason = null,
            scan = scan,
            stillFound = true
        )
    }

    private fun fixed(intentId: String, fixId: String, confidence: Double, state: DeviceState) =
        Reply.Fixed(
            catalog.intent(intentId),
            catalog.fix(fixId),
            next(intentId, confidence, state),
            diagnoser.scan(intentId, state)
        )
}
