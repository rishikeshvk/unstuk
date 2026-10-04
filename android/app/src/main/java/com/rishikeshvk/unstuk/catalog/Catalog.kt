package com.rishikeshvk.unstuk.catalog

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class Risk {
    @SerialName("low")
    LOW,

    @SerialName("medium")
    MEDIUM,

    @SerialName("high")
    HIGH
}

/** The executor ladder (AGENTS.md invariant 5), declared in the order it is tried. */
@Serializable
enum class Rung {
    @SerialName("direct")
    DIRECT,

    @SerialName("panel")
    PANEL,

    @SerialName("accessibility")
    ACCESSIBILITY,

    @SerialName("guided")
    GUIDED
}

/** A cause worth checking for an intent: when [check] holds on a fresh snapshot, [fix] is the remedy. */
@Serializable
data class Cause(val check: String, val fix: String)

/**
 * One issue a user can complain about. [option] is the plain-language text the model chooses between;
 * [fallback] is the guide card shown when no cause holds.
 */
@Serializable
data class IntentEntry(
    val id: String,
    val option: String,
    val causes: List<Cause>,
    val fallback: List<String>
)

@Serializable
data class FixEntry(
    val id: String,
    val label: String,
    val risk: Risk,
    val rungs: List<Rung>,
    val guide: List<String>
)

data class Catalog(val intents: List<IntentEntry>, val fixes: List<FixEntry>) {
    private val intentsById = intents.associateBy { it.id }
    private val fixesById = fixes.associateBy { it.id }

    fun intent(id: String): IntentEntry = intentsById.getValue(id)

    fun fix(id: String): FixEntry = fixesById.getValue(id)
}
