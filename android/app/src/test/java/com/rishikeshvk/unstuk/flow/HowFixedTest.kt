package com.rishikeshvk.unstuk.flow

import com.rishikeshvk.unstuk.catalog.Rung
import com.rishikeshvk.unstuk.trace.TraceEvent
import org.junit.Assert.assertEquals
import org.junit.Test

class HowFixedTest {
    private fun event(ts: Long, step: String, outcome: String) =
        TraceEvent(ts, "t", "complaint", step, outcome)

    @Test
    fun `lists each rung tried and the fresh read, with how long each took`() {
        val events = listOf(
            event(0, "precondition", "needs_change"),
            event(5, "direct_api", "called"),
            event(14, "rung_direct", "needs_guidance"),
            event(300, "find_tile", "found"),
            event(426, "rung_accessibility", "verified"),
            event(464, "verify", "reached"),
            event(470, "reply", "verified")
        )
        assertEquals(
            listOf(
                FixStep(Rung.DIRECT, ok = false, millis = 14),
                FixStep(Rung.ACCESSIBILITY, ok = true, millis = 412),
                FixStep(null, ok = true, millis = 38)
            ),
            HowFixed.from(events)
        )
    }

    @Test
    fun `only the last run in a conversation counts`() {
        val events = listOf(
            event(0, "precondition", "needs_change"),
            event(10, "rung_direct", "verified"),
            event(20, "verify", "reached"),
            event(100, "precondition", "needs_change"),
            event(130, "rung_direct", "verified"),
            event(136, "verify", "reached")
        )
        assertEquals(
            listOf(FixStep(Rung.DIRECT, true, 30), FixStep(null, true, 6)),
            HowFixed.from(events)
        )
    }

    @Test
    fun `a conversation with no run has no steps`() {
        assertEquals(emptyList<FixStep>(), HowFixed.from(listOf(event(0, "decide", "none"))))
    }
}
