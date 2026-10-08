package com.rishikeshvk.unstuk.decide

/**
 * A Choice answer: a probability per intent id, and for the complaint being out of scope. The intents share
 * what out of scope leaves. Empty intents mean nothing matched.
 */
data class IntentChoice(val probabilities: Map<String, Double>, val outOfScope: Double = 0.0) {
    val top: Map.Entry<String, Double>? = probabilities.maxByOrNull { it.value }

    /** Nothing to act on: no intent, or out of scope is likelier than the best one. */
    val declines: Boolean = top == null || outOfScope > top.value

    /** The [count] most likely intents, best first, to offer in a clarifying question. */
    fun leaders(count: Int): List<String> =
        probabilities.entries.sortedByDescending { it.value }.take(count).map { it.key }
}
