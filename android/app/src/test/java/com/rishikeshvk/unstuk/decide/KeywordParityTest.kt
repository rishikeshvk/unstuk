package com.rishikeshvk.unstuk.decide

import com.rishikeshvk.unstuk.catalog.CatalogTestFiles
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Test

@Serializable
private data class ParityCase(val complaint: String, val probabilities: Map<String, Double>)

@Serializable
private data class ParityFixture(val cases: List<ParityCase>)

/** The Python port in `ml/` checks the same fixture, so the two matchers can't drift apart. */
class KeywordParityTest {
    private val matcher = KeywordMatcher(CatalogTestFiles.keywords)
    private val json = Json { ignoreUnknownKeys = true }

    @Test
    fun `matches the shared parity fixture`() {
        val text = javaClass.getResource("/keyword-parity.json")!!.readText()
        for (case in json.decodeFromString<ParityFixture>(text).cases) {
            val got = matcher.choose(case.complaint).probabilities
            assertEquals(case.complaint, case.probabilities.keys, got.keys)
            for ((intent, p) in case.probabilities) {
                assertEquals(case.complaint, p, got.getValue(intent), 1e-9)
            }
        }
    }
}
