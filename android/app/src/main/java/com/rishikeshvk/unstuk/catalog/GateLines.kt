package com.rishikeshvk.unstuk.catalog

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** The risk gate's lines from `catalog/gate.json`, tuned on dev in M6 and read by training too. */
@Serializable
data class GateLines(
    @SerialName("automatic_at") val automaticAt: Double,
    @SerialName("clarify_below") val clarifyBelow: Double,
    /** Clarify when the top two intents are closer than this, however sure the top one is. */
    @SerialName("clarify_margin") val clarifyMargin: Double
)
