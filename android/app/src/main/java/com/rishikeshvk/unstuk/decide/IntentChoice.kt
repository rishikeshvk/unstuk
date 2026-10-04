package com.rishikeshvk.unstuk.decide

/**
 * A Choice answer over intents: a probability per intent id, the same shape the model's answer will have.
 * Empty when nothing matched.
 */
data class IntentChoice(val probabilities: Map<String, Double>) {
    val top: Map.Entry<String, Double>? = probabilities.maxByOrNull { it.value }

    /** The [count] most likely intents, best first, to offer in a clarifying question. */
    fun leaders(count: Int): List<String> =
        probabilities.entries.sortedByDescending { it.value }.take(count).map { it.key }
}
