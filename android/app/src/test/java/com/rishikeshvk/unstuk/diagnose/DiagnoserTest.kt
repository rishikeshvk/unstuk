package com.rishikeshvk.unstuk.diagnose

import android.media.AudioManager
import com.rishikeshvk.unstuk.catalog.CatalogTestFiles
import com.rishikeshvk.unstuk.state.Volume
import com.rishikeshvk.unstuk.state.fineDeviceState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class DiagnoserTest {
    private val diagnoser = Diagnoser(CatalogTestFiles.catalog)

    @Test
    fun `finds nothing when the phone is fine`() {
        for (intent in CatalogTestFiles.catalog.intents.filter { it.id != "reset_network" }) {
            assertNull(intent.id, diagnoser.diagnose(intent.id, fineDeviceState))
        }
    }

    @Test
    fun `picks the first cause that holds, in catalog order`() {
        val state = fineDeviceState.copy(
            ringerMode = AudioManager.RINGER_MODE_SILENT,
            ringVolume = Volume(0, 7)
        )
        assertEquals("ringer_normal", diagnoser.diagnose("phone_not_ringing", state)?.id)
    }

    @Test
    fun `airplane mode comes before the data checks it would otherwise trigger`() {
        val state = fineDeviceState.copy(
            airplaneModeOn = true,
            online = false,
            wifiOn = false,
            mobileDataOn = false
        )
        assertEquals("airplane_off", diagnoser.diagnose("no_internet", state)?.id)
    }

    @Test
    fun `wifi off is not a cause while the phone is online over mobile data`() {
        assertNull(diagnoser.diagnose("no_internet", fineDeviceState.copy(wifiOn = false)))
    }

    @Test
    fun `an unreadable setting never counts as a cause`() {
        assertNull(
            diagnoser.diagnose(
                "colours_wrong",
                fineDeviceState.copy(inversionOn = null, greyscaleOn = null)
            )
        )
        assertNull(
            diagnoser.diagnose(
                "no_internet",
                fineDeviceState.copy(online = false, mobileDataOn = null)
            )
        )
    }

    @Test
    fun `reset network always applies, so the gate decides how`() {
        assertEquals("reset_network", diagnoser.diagnose("reset_network", fineDeviceState)?.id)
    }

    @Test
    fun `the scan lists real checks only`() {
        assertEquals(emptyList<ScanRow>(), diagnoser.scan("reset_network", fineDeviceState))
        assertEquals(
            listOf("inversion_off", "greyscale_off"),
            diagnoser.scan("colours_wrong", fineDeviceState).map { it.fix.id }
        )
    }
}
