package com.rishikeshvk.unstuk.selector

/**
 * Compares the text before the first ',' or '.' with each label, ignoring case. Tiles append their state after
 * the label ("Do Not Disturb. On", "Wi-Fi, Off"), while longer phrases ("Do Not Disturb is on") don't match.
 */
fun matchesLabel(text: CharSequence?, labels: List<String>): Boolean {
    if (text.isNullOrBlank()) return false
    val lead = text.split(',', '.').first().trim()
    return labels.any { it.equals(lead, ignoreCase = true) }
}
