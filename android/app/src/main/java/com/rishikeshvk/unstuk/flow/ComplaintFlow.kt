package com.rishikeshvk.unstuk.flow

import android.content.Context
import com.rishikeshvk.unstuk.catalog.CatalogLoader
import com.rishikeshvk.unstuk.decide.DecisionModel
import com.rishikeshvk.unstuk.decide.RiskGate
import com.rishikeshvk.unstuk.decide.StateText
import com.rishikeshvk.unstuk.fix.FixRunner
import com.rishikeshvk.unstuk.state.DeviceStateReader
import com.rishikeshvk.unstuk.trace.TraceWriter
import com.rishikeshvk.unstuk.trace.Tracer
import java.io.File

private const val TRACE_ACTION = "complaint"

/**
 * The pipeline from a complaint to a reply: decide, gate, diagnose, run, verify. Every stage writes a trace line
 * under the conversation's trial id; the complaint text itself is never written (it may be a real user's).
 */
class ComplaintFlow(context: Context) : AutoCloseable {
    private val catalog = CatalogLoader.load(context.assets)
    private val assets = context.assets

    // Loaded on first use, which [warmUp] brings forward to app start; a complaint before then waits for it.
    private val loading = lazy { DecisionModel.load(assets) }
    private val model by loading
    private val stateText by lazy { StateText(catalog, model.manifest.stateChecks) }
    private val triage = Triage(catalog, RiskGate(CatalogLoader.loadGate(context.assets)))
    private val reader = DeviceStateReader(context)
    private val runner = FixRunner(context)
    private val traces = TraceWriter(File(context.filesDir, "traces"))

    /** Slow: call it once, off the main thread. */
    fun warmUp() {
        stateText
    }

    fun start(complaint: String, trialId: String): Reply {
        val tracer = tracer(trialId)
        val state = reader.read()
        val text = stateText.render(state)
        val started = System.nanoTime()
        val choice = model.decide(complaint, text)
        val millis = (System.nanoTime() - started) / 1_000_000
        tracer.step(
            "decide",
            choice.top?.key?.takeUnless { choice.declines } ?: "out_of_scope",
            detail = (choice.probabilities + ("out_of_scope" to choice.outOfScope)).entries
                .sortedByDescending { it.value }
                .joinToString { "${it.key}=${"%.2f".format(it.value)}" } + "; ${millis}ms"
        )
        return traced(triage.triage(choice, state), tracer)
    }

    /** The user answered a clarifying question, so the intent is theirs, not a guess. */
    fun choose(intentId: String, trialId: String): Reply {
        val tracer = tracer(trialId)
        tracer.step("clarified", intentId)
        return traced(triage.forIntent(intentId, USER_CHOSEN, reader.read()), tracer)
    }

    suspend fun run(intentId: String, fixId: String, confidence: Double, trialId: String): Reply {
        val tracer = tracer(trialId)
        val outcome = runner.run(catalog.fix(fixId), tracer)
        return traced(triage.afterRun(outcome, intentId, fixId, confidence, reader.read()), tracer)
    }

    /** The user followed a guide and asks Unstuk to look again. */
    fun recheck(intentId: String, fixId: String, confidence: Double, trialId: String): Reply {
        val tracer = tracer(trialId)
        tracer.step("recheck", fixId)
        return traced(triage.recheck(intentId, fixId, confidence, reader.read()), tracer)
    }

    /** The ladder steps of the last fix run in this conversation, from its trace. */
    fun howFixed(trialId: String): List<FixStep> = HowFixed.from(traces.read(trialId))

    private fun tracer(trialId: String) = Tracer(traces, trialId, TRACE_ACTION)

    private fun traced(reply: Reply, tracer: Tracer): Reply {
        tracer.step("reply", reply.traceName, detail = reply.subject())
        return reply
    }

    private fun Reply.subject(): String? = when (this) {
        is Reply.Clarify -> intents.joinToString { it.id }
        is Reply.AllClear -> intent.id
        is Reply.Guide ->
            listOfNotNull(fix.id, reason, "still_found".takeIf { stillFound }).joinToString(": ")
        is Reply.Confirm -> "${intent.id}/${fix.id}"
        is Reply.Run -> "${intent.id}/${fix.id}"
        is Reply.Fixed -> fix.id + (next?.let { " next=${it.traceName}" } ?: "")
        is Reply.AlreadyFine -> fix.id
        Reply.NeedsUnlock, Reply.Decline -> null
    }

    override fun close() {
        if (loading.isInitialized()) model.close()
    }

    companion object {
        const val USER_CHOSEN = 1.0
    }
}
