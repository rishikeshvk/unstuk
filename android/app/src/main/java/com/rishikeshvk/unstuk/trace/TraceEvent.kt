package com.rishikeshvk.unstuk.trace

import kotlinx.serialization.Serializable

/** One executor step. `strategy` names how a node was found (resource-id, label, ...) when the step looked for one. */
@Serializable
data class TraceEvent(
    val ts: Long,
    val trialId: String,
    val action: String,
    val step: String,
    val outcome: String,
    val strategy: String? = null
)
