package com.rishikeshvk.unstuk.catalog

import java.io.File

/** The repository's `catalog/`, read from the app module's directory, where Gradle runs unit tests. */
object CatalogTestFiles {
    private val dir = File("../../catalog")

    val catalog: Catalog by lazy {
        CatalogLoader.parse(text(CatalogLoader.INTENTS), text(CatalogLoader.FIXES))
    }

    val keywords: Map<String, List<String>> by lazy {
        CatalogLoader.parseKeywords(text(CatalogLoader.KEYWORDS))
    }

    private fun text(name: String) = File(dir, name).readText()
}
