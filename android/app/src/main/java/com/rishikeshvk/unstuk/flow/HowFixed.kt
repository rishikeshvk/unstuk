package com.rishikeshvk.unstuk.flow

import com.rishikeshvk.unstuk.catalog.Rung
import com.rishikeshvk.unstuk.trace.TraceEvent

/** One step of the executor ladder as the user can see it. [rung] is null for the final fresh read. */
data class FixStep(val rung: Rung?, val ok: Boolean, val millis: Long)

/** Reads the last run of a fix back out of its trace, for the "How I fixed it" timeline. */
object HowFixed {
    private const val RUNG_PREFIX = "rung_"

    fun from(events: List<TraceEvent>): List<FixStep> {
        // A conversation can run several fixes under one trial id; each run starts with its precondition.
        val start = events.indexOfLast { it.step == "precondition" }
        if (start < 0) return emptyList()
        var previous = events[start].ts
        return events.drop(start + 1).mapNotNull { event ->
            val step = toStep(event, event.ts - previous) ?: return@mapNotNull null
            previous = event.ts
            step
        }
    }

    private fun toStep(event: TraceEvent, millis: Long): FixStep? = when {
        event.step.startsWith(RUNG_PREFIX) -> FixStep(
            Rung.valueOf(event.step.removePrefix(RUNG_PREFIX).uppercase()),
            ok = event.outcome == "verified",
            millis = millis
        )
        event.step == "verify" -> FixStep(null, ok = event.outcome == "reached", millis = millis)
        else -> null
    }
}
