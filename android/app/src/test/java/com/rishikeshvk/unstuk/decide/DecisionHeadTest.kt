package com.rishikeshvk.unstuk.decide

import kotlin.math.exp
import org.junit.Assert.assertEquals
import org.junit.Test

class DecisionHeadTest {
    private val manifest = ModelManifest(
        intents = listOf("a", "b"),
        stateChecks = emptyList(),
        dimensions = 2,
        scale = 20.0,
        choiceTemperature = 2.0,
        noulTemperature = 1.5,
        maxTokens = 128
    )
    private val head = DecisionHead(manifest, listOf(floatArrayOf(1f, 0f), floatArrayOf(0f, 1f)))

    @Test
    fun `intents share what out of scope leaves, by the scaled cosine over the temperature`() {
        val choice = head.decide(floatArrayOf(0.6f, 0.8f), noulLogit = 0f)

        // Logits 20 * 0.6 / 2 = 6 and 20 * 0.8 / 2 = 8; Noul 0 is a half.
        val b = 1 / (1 + exp(-2.0))
        assertEquals(0.5, choice.outOfScope, 1e-12)
        assertEquals(0.5 * (1 - b), choice.probabilities.getValue("a"), 1e-6)
        assertEquals(0.5 * b, choice.probabilities.getValue("b"), 1e-6)
    }

    @Test
    fun `a high Noul logit, softened by its temperature, declines`() {
        val choice = head.decide(floatArrayOf(1f, 0f), noulLogit = 6f)

        assertEquals(1 / (1 + exp(-4.0)), choice.outOfScope, 1e-6)
        assertEquals(true, choice.declines)
    }
}
