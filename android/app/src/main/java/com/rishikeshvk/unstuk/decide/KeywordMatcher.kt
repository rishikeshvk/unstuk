package com.rishikeshvk.unstuk.decide

private val NON_WORD = Regex("[^a-z0-9]+")

/**
 * The M2 stand-in for the model. Each intent's score is the number of its phrases found in the complaint, and
 * its probability is its share of all hits. Those numbers aren't calibrated; they only have the right shape.
 */
class KeywordMatcher(rules: Map<String, List<String>>) {
    private val phrases = rules.mapValues { (_, list) -> list.map(::normalize) }

    fun choose(complaint: String): IntentChoice {
        val text = normalize(complaint)
        val hits = phrases
            .mapValues { (_, list) -> list.count { it in text } }
            .filterValues { it > 0 }
        val total = hits.values.sum().toDouble()
        return IntentChoice(hits.mapValues { it.value / total })
    }

    // Padded with spaces so a phrase only matches whole words ("ring" must not match "bring").
    private fun normalize(text: String) = " " + text.lowercase().replace(NON_WORD, " ").trim() + " "
}
