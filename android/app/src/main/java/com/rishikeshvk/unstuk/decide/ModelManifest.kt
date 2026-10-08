package com.rishikeshvk.unstuk.decide

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * `assets/model/model.json`, written by `unstuk-export assets`: what the graph's numbers mean. Its sha256s are
 * for the build's check and aren't read here.
 */
@Serializable
data class ModelManifest(
    /** Intent ids in the order of their vectors in `options.bin`. */
    val intents: List<String>,
    /** The checks training showed the model, in the order its state text lists them. */
    @SerialName("state_checks") val stateChecks: List<String>,
    val dimensions: Int,
    /** Turns a cosine into a Choice logit. */
    val scale: Double,
    @SerialName("choice_temperature") val choiceTemperature: Double,
    @SerialName("noul_temperature") val noulTemperature: Double,
    @SerialName("max_tokens") val maxTokens: Int
)
