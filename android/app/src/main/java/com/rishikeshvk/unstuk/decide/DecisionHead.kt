package com.rishikeshvk.unstuk.decide

import kotlin.math.exp

/**
 * M6's heads on top of the graph's outputs, as `decision_scoring.scored` computes them in training. Choice is a
 * softmax over the scaled cosines with the complaint, Noul a sigmoid, and the intents share what out of scope
 * leaves. Both vectors have unit length, so a dot product is the cosine.
 */
class DecisionHead(private val manifest: ModelManifest, private val options: List<FloatArray>) {
    init {
        require(options.size == manifest.intents.size) { "one option vector per intent" }
    }

    fun decide(vector: FloatArray, noulLogit: Float): IntentChoice {
        val logits = options.map { manifest.scale * dot(vector, it) / manifest.choiceTemperature }
        val top = logits.max()
        // Shifted by the largest logit so exp can't overflow; the softmax is unchanged.
        val weights = logits.map { exp(it - top) }
        val total = weights.sum()
        val outOfScope = 1 / (1 + exp(-noulLogit / manifest.noulTemperature))
        val probabilities = manifest.intents.zip(weights).associate { (intent, weight) ->
            intent to (1 - outOfScope) * weight / total
        }
        return IntentChoice(probabilities, outOfScope)
    }

    private fun dot(a: FloatArray, b: FloatArray): Double {
        var sum = 0.0
        for (i in a.indices) sum += a[i].toDouble() * b[i]
        return sum
    }
}
