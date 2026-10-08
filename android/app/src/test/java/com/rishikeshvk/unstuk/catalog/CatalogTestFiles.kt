package com.rishikeshvk.unstuk.catalog

import java.io.File
import kotlinx.serialization.json.Json

/** The repository's `catalog/`, read from the app module's directory, where Gradle runs unit tests. */
object CatalogTestFiles {
    private val dir = File("../../catalog")

    val catalog: Catalog by lazy {
        CatalogLoader.parse(text(CatalogLoader.INTENTS), text(CatalogLoader.FIXES))
    }

    val keywords: Map<String, List<String>> by lazy {
        CatalogLoader.parseKeywords(text(CatalogLoader.KEYWORDS))
    }

    val gate: GateLines by lazy { CatalogLoader.parseGate(text(CatalogLoader.GATE)) }

    /** IDs that data refers to, by kind; see `ids.lock`. */
    val idsLock: Map<String, List<String>> by lazy { Json.decodeFromString(text("ids.lock")) }

    private fun text(name: String) = File(dir, name).readText()
}
