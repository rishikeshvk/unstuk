package com.rishikeshvk.unstuk.decide

import com.rishikeshvk.unstuk.catalog.FixEntry
import com.rishikeshvk.unstuk.catalog.Risk
import com.rishikeshvk.unstuk.catalog.Rung
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class RiskGateTest {
    private val gate = RiskGate(autoThreshold = 0.8, clarifyBelow = 0.5)

    private fun fix(risk: Risk) = FixEntry("f", "Fix", risk, listOf(Rung.GUIDED), listOf("step"))

    @Test
    fun `routes each risk and confidence to the right execution`() {
        val cases = listOf(
            Triple(Risk.LOW, 1.0, Execution.AUTOMATIC),
            Triple(Risk.LOW, 0.8, Execution.AUTOMATIC),
            Triple(Risk.LOW, 0.79, Execution.CONFIRM),
            Triple(Risk.MEDIUM, 1.0, Execution.CONFIRM),
            Triple(Risk.HIGH, 1.0, Execution.GUIDED_ONLY),
            Triple(Risk.HIGH, 0.6, Execution.GUIDED_ONLY)
        )
        for ((risk, confidence, expected) in cases) {
            assertEquals("$risk @ $confidence", expected, gate.execution(fix(risk), confidence))
        }
    }

    @Test
    fun `too uncertain below the clarify line`() {
        assertTrue(gate.isTooUncertain(0.49))
        assertFalse(gate.isTooUncertain(0.5))
    }
}
