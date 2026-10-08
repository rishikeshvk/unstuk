package com.rishikeshvk.unstuk.catalog

import android.content.res.AssetManager
import kotlinx.serialization.json.Json

/** Reads `catalog/` at the repository root, which the build adds as an assets directory. */
object CatalogLoader {
    const val INTENTS = "intents.json"
    const val FIXES = "fixes.json"
    const val KEYWORDS = "keywords.json"
    const val GATE = "gate.json"

    fun load(assets: AssetManager): Catalog = parse(assets.text(INTENTS), assets.text(FIXES))

    fun loadKeywords(assets: AssetManager): Map<String, List<String>> =
        parseKeywords(assets.text(KEYWORDS))

    fun parse(intents: String, fixes: String) =
        Catalog(Json.decodeFromString(intents), Json.decodeFromString(fixes))

    fun loadGate(assets: AssetManager): GateLines = parseGate(assets.text(GATE))

    fun parseKeywords(text: String): Map<String, List<String>> = Json.decodeFromString(text)

    fun parseGate(text: String): GateLines = Json.decodeFromString(text)

    private fun AssetManager.text(name: String) = open(name).bufferedReader().use { it.readText() }
}
