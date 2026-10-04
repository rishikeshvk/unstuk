package com.rishikeshvk.unstuk.selector

import android.content.res.AssetManager
import kotlinx.serialization.json.Json

/** Loads the OEM selector file for this device; stock Android (pixel.json) is the default. */
object SelectorLoader {
    fun fileFor(manufacturer: String) = when (manufacturer.lowercase()) {
        "motorola" -> "motorola.json"
        else -> "pixel.json"
    }

    fun load(assets: AssetManager, manufacturer: String): Selectors = parse(
        assets.open("selectors/${fileFor(manufacturer)}").bufferedReader().use {
            it.readText()
        }
    )

    fun parse(text: String): Selectors = Json.decodeFromString(text)
}
