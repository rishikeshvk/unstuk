package com.rishikeshvk.unstuk.decide

import com.rishikeshvk.unstuk.catalog.CatalogTestFiles
import com.rishikeshvk.unstuk.diagnose.Checks
import java.io.File
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** The committed manifest against the catalog the app ships with. */
class ModelManifestTest {
    private val manifest = Json { ignoreUnknownKeys = true }
        .decodeFromString<ModelManifest>(File("src/main/assets/model/model.json").readText())

    @Test
    fun `offers every catalog intent`() {
        assertEquals(
            CatalogTestFiles.catalog.intents.map {
                it.id
            }.toSet(),
            manifest.intents.toSet()
        )
    }

    @Test
    fun `reads only checks the app can evaluate`() {
        assertTrue(Checks.all.keys.containsAll(manifest.stateChecks))
        assertTrue(Checks.ALWAYS !in manifest.stateChecks)
    }
}
