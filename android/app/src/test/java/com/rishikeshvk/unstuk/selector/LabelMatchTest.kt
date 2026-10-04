package com.rishikeshvk.unstuk.selector

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class LabelMatchTest {
    private val dnd = listOf("Do Not Disturb")
    private val airplane = listOf("Airplane mode", "Aeroplane mode")

    @Test
    fun `matches a tile label followed by its state`() {
        assertTrue(matchesLabel("Do Not Disturb. On", dnd))
        assertTrue(matchesLabel("Wi-Fi, Off", listOf("Wi-Fi")))
        assertTrue(matchesLabel("Airplane mode.", airplane))
    }

    @Test
    fun `matches any label variant ignoring case`() {
        assertTrue(matchesLabel("aeroplane mode", airplane))
    }

    @Test
    fun `rejects longer phrases and other tiles`() {
        assertFalse(matchesLabel("Do Not Disturb is on", dnd))
        assertFalse(matchesLabel("Mobile data", airplane))
    }

    @Test
    fun `rejects missing text`() {
        assertFalse(matchesLabel(null, dnd))
        assertFalse(matchesLabel("  ", dnd))
    }
}
