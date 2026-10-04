package com.rishikeshvk.unstuk.trace

/** Writes the steps of one action run under one trial id. */
class Tracer(
    private val writer: TraceWriter,
    val trialId: String,
    private val action: String,
    private val clock: () -> Long = System::currentTimeMillis
) {
    fun step(step: String, outcome: String, strategy: String? = null, detail: String? = null) =
        writer.append(TraceEvent(clock(), trialId, action, step, outcome, strategy, detail))
}
