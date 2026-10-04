package com.rishikeshvk.unstuk.selector

import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class SelectorLoaderTest {
    private val selectorDir = File("src/main/assets/selectors")

    @Test
    fun `picks the Motorola file for Motorola and stock Android for everything else`() {
        assertEquals("motorola.json", SelectorLoader.fileFor("motorola"))
        assertEquals("pixel.json", SelectorLoader.fileFor("Google"))
        assertEquals("pixel.json", SelectorLoader.fileFor("samsung"))
    }

    @Test
    fun `every selector file reaches every target through a tile or a Settings path`() {
        val files = selectorDir.listFiles { f -> f.extension == "json" }.orEmpty()
        assertTrue("no selector files found", files.isNotEmpty())

        for (file in files) {
            val selectors = SelectorLoader.parse(file.readText())
            for (target in SettingTarget.entries) {
                val tile = selectors.quickSettings.tiles[target]
                val path = selectors.settings.paths[target].orEmpty()
                assertTrue(
                    "${file.name}: no tile or Settings path for $target",
                    tile != null || path.isNotEmpty()
                )
                assertTrue("${file.name}: unusable tile for $target", tile?.isUsable() != false)
                assertTrue(
                    "${file.name}: unusable Settings path for $target",
                    path.all {
                        it.isUsable()
                    }
                )
                val dialog = selectors.quickSettings.tileDialogs[target].orEmpty()
                assertTrue(
                    "${file.name}: unusable tile dialog for $target",
                    dialog.all {
                        it.isUsable()
                    }
                )
            }
        }
    }

    private fun NodeSelector.isUsable() = resourceIds.isNotEmpty() || labels.isNotEmpty()
}
