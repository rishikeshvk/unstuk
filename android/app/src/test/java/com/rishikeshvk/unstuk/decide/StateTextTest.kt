package com.rishikeshvk.unstuk.decide

import android.app.NotificationManager
import com.rishikeshvk.unstuk.catalog.CatalogTestFiles
import com.rishikeshvk.unstuk.state.fineDeviceState
import org.junit.Assert.assertEquals
import org.junit.Test

class StateTextTest {
    private val catalog = CatalogTestFiles.catalog
    private val text = StateText(catalog, listOf("airplane_on", "dnd_on", "talkback_on"))

    @Test
    fun `a fine phone has no state text`() {
        assertEquals("", text.render(fineDeviceState))
    }

    @Test
    fun `lists the findings that hold, in the given order`() {
        val state = fineDeviceState.copy(
            interruptionFilter = NotificationManager.INTERRUPTION_FILTER_PRIORITY,
            airplaneModeOn = true
        )

        val expected = listOf("airplane_off", "dnd_off").joinToString(" ") {
            catalog.fix(it).finding
        }
        assertEquals(expected, text.render(state))
    }

    @Test
    fun `a check the model was not trained on is left out, even when it holds`() {
        assertEquals("", text.render(fineDeviceState.copy(autoRotateOn = false)))
    }
}
