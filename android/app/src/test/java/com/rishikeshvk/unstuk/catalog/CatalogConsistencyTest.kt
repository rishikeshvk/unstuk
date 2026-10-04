package com.rishikeshvk.unstuk.catalog

import com.rishikeshvk.unstuk.diagnose.Checks
import com.rishikeshvk.unstuk.fix.FixSpecs
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class CatalogConsistencyTest {
    private val catalog = CatalogTestFiles.catalog

    @Test
    fun `intent and fix ids are unique`() {
        assertEquals(catalog.intents.size, catalog.intents.map { it.id }.toSet().size)
        assertEquals(catalog.fixes.size, catalog.fixes.map { it.id }.toSet().size)
    }

    @Test
    fun `every check the catalog names is implemented and every implemented check is used`() {
        val named = catalog.intents.flatMap { it.causes }.map { it.check }.toSet()
        assertEquals(named, Checks.all.keys)
    }

    @Test
    fun `every fix has an executor spec and every spec is in the catalog`() {
        assertEquals(catalog.fixes.map { it.id }.toSet(), FixSpecs.all.keys)
    }

    @Test
    fun `every fix is the remedy for some cause`() {
        val used = catalog.intents.flatMap { it.causes }.map { it.fix }.toSet()
        assertEquals(catalog.fixes.map { it.id }.toSet(), used)
    }

    @Test
    fun `each fix lists exactly its spec's rungs, in ladder order, ending in guided steps`() {
        for (fix in catalog.fixes) {
            assertEquals(fix.id, FixSpecs.get(fix.id).rungs, fix.rungs)
            assertEquals(fix.id, fix.rungs.sorted(), fix.rungs)
        }
    }

    @Test
    fun `high-risk fixes are guided only`() {
        catalog.fixes.filter { it.risk == Risk.HIGH }.forEach {
            assertEquals(it.id, listOf(Rung.GUIDED), it.rungs)
        }
    }

    @Test
    fun `every fix has guide steps and every intent with no sure cause has a fallback card`() {
        catalog.fixes.forEach { assertTrue(it.id, it.guide.isNotEmpty()) }
        catalog.intents.filter { intent -> intent.causes.none { it.check == "always" } }
            .forEach { assertTrue(it.id, it.fallback.isNotEmpty()) }
    }

    @Test
    fun `keyword rules cover exactly the catalog's intents`() {
        assertEquals(catalog.intents.map { it.id }.toSet(), CatalogTestFiles.keywords.keys)
    }
}
