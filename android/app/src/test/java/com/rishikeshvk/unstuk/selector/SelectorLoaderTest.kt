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
    fun `every selector file covers every target in Quick Settings and Settings`() {
        val files = selectorDir.listFiles { f -> f.extension == "json" }.orEmpty()
        assertTrue("no selector files found", files.isNotEmpty())

        for (file in files) {
            val selectors = SelectorLoader.parse(file.readText())
            for (target in SettingTarget.entries) {
                val tile = selectors.quickSettings.tiles[target]
                assertTrue("${file.name}: no tile for $target", tile != null && tile.isUsable())
                val path = selectors.settings.paths[target].orEmpty()
                assertTrue(
                    "${file.name}: no Settings path for $target",
                    path.isNotEmpty() && path.all { it.isUsable() }
                )
            }
        }
    }

    private fun NodeSelector.isUsable() = resourceIds.isNotEmpty() || labels.isNotEmpty()
}
