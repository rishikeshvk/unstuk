package com.rishikeshvk.unstuk.decide

import com.rishikeshvk.unstuk.catalog.CatalogTestFiles
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * The complaints here are test fixtures we wrote, not real user messages or training seeds (invariant 9).
 * They check the matcher's mechanics and that each intent's rules fire on an obvious phrasing.
 */
class KeywordMatcherTest {
    private val matcher = KeywordMatcher(CatalogTestFiles.keywords)

    @Test
    fun `an obvious complaint per intent goes to that intent`() {
        val fixtures = mapOf(
            "no_internet" to "My internet is not working",
            "wifi_no_load" to "Wifi connected but pages don't load",
            "phone_not_ringing" to "Phone doesn't ring",
            "cant_hear_call" to "I can't hear the person",
            "notifications_missing" to "WhatsApp messages late",
            "talkback_on" to "Phone keeps talking to me",
            "colours_wrong" to "Screen went black and white",
            "screen_too_dim" to "Screen is too dark",
            "screen_turns_off_fast" to "Screen goes off quickly",
            "screen_wont_rotate" to "Screen won't go sideways",
            "text_too_small" to "Letters are tiny",
            "bluetooth_earphones" to "My earbuds won't pair",
            "app_permission" to "Camera not working in Zoom",
            "wrong_time" to "The clock shows the wrong time",
            "reset_network" to "Please reset network settings"
        )
        assertEquals(CatalogTestFiles.catalog.intents.map { it.id }.toSet(), fixtures.keys)
        for ((intent, complaint) in fixtures) {
            assertEquals(complaint, intent, matcher.choose(complaint).top?.key)
        }
    }

    @Test
    fun `probabilities are each intent's share of the hits`() {
        val choice = matcher.choose("bluetooth earbuds and no ring")
        assertEquals(1.0, choice.probabilities.values.sum(), 1e-9)
        assertEquals(2.0 / 3, choice.probabilities.getValue("bluetooth_earphones"), 1e-9)
    }

    @Test
    fun `phrases match whole words only`() {
        assertNull(matcher.choose("bring me a pizza").top)
    }

    @Test
    fun `nothing matched gives an empty choice`() {
        assertEquals(
            emptyMap<String, Double>(),
            matcher.choose("What's the capital of France?").probabilities
        )
    }
}
