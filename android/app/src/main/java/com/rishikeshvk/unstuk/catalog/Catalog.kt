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

/** The topics a user can browse instead of typing, in the order the app shows them. */
@Serializable
enum class Area {
    @SerialName("internet")
    INTERNET,

    @SerialName("calls")
    CALLS,

    @SerialName("screen")
    SCREEN,

    @SerialName("messages")
    MESSAGES,

    @SerialName("bluetooth")
    BLUETOOTH,

    @SerialName("apps")
    APPS
}

/** A cause worth checking for an intent: when [check] holds on a fresh snapshot, [fix] is the remedy. */
@Serializable
data class Cause(val check: String, val fix: String)

/**
 * One issue a user can complain about. [option] is the plain-language text the model chooses between;
 * [area] is the topic it is browsed under; [fallback] is the guide card shown when no cause holds.
 */
@Serializable
data class IntentEntry(
    val id: String,
    val option: String,
    val area: Area,
    val causes: List<Cause>,
    val fallback: List<String>
)

/**
 * A remedy. [subject] names the setting in a diagnosis scan, [finding] (and the optional [why]) says what is
 * wrong, and [done] is the success line, shown only after a fresh read confirmed the fix.
 */
@Serializable
data class FixEntry(
    val id: String,
    val label: String,
    val subject: String,
    val finding: String,
    val why: String? = null,
    val done: String,
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
