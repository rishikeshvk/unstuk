package com.rishikeshvk.unstuk.flow

import com.rishikeshvk.unstuk.catalog.CatalogTestFiles
import com.rishikeshvk.unstuk.decide.IntentChoice
import com.rishikeshvk.unstuk.state.fineDeviceState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class TriageTest {
    private val triage = Triage(CatalogTestFiles.catalog)

    @Test
    fun `nothing matched declines`() {
        assertTrue(triage.triage(IntentChoice(emptyMap()), fineDeviceState) is Reply.Decline)
    }

    @Test
    fun `a split decision asks which issue it is, best first`() {
        val reply = triage.triage(
            IntentChoice(
                mapOf(
                    "screen_too_dim" to 0.4,
                    "colours_wrong" to 0.35,
                    "text_too_small" to 0.25
                )
            ),
            fineDeviceState
        )
        assertEquals(
            listOf("screen_too_dim", "colours_wrong", "text_too_small"),
            (reply as Reply.Clarify).intents.map { it.id }
        )
    }

    @Test
    fun `a sure low-risk fix runs without asking`() {
        val reply = triage.triage(
            IntentChoice(mapOf("no_internet" to 1.0)),
            fineDeviceState.copy(airplaneModeOn = true)
        )
        assertEquals("airplane_off", (reply as Reply.Run).fix.id)
    }

    @Test
    fun `a low-risk fix below the threshold asks first`() {
        val reply = triage.triage(
            IntentChoice(mapOf("no_internet" to 0.6, "wrong_time" to 0.4)),
            fineDeviceState.copy(airplaneModeOn = true)
        )
        assertEquals("airplane_off", (reply as Reply.Confirm).fix.id)
    }

    @Test
    fun `a medium-risk fix asks first even when sure`() {
        val reply = triage.triage(
            IntentChoice(mapOf("talkback_on" to 1.0)),
            fineDeviceState.copy(
                enabledAccessibilityServices = listOf(
                    "com.google.android.marvin.talkback/.TalkBackService"
                )
            )
        )
        assertEquals("talkback_off", (reply as Reply.Confirm).fix.id)
    }

    @Test
    fun `a high-risk fix only gets guided steps`() {
        val reply = triage.triage(IntentChoice(mapOf("reset_network" to 1.0)), fineDeviceState)
        assertEquals("reset_network", (reply as Reply.Guide).fix.id)
    }

    @Test
    fun `no cause holding gives the intent's own guide card`() {
        val reply = triage.triage(IntentChoice(mapOf("phone_not_ringing" to 1.0)), fineDeviceState)
        assertEquals("phone_not_ringing", (reply as Reply.AllClear).intent.id)
    }

    @Test
    fun `the next cause after a fix is offered, never run`() {
        val state = fineDeviceState.copy(online = false, wifiOn = false, mobileDataOn = false)
        val next = triage.next("no_internet", 1.0, state)
        assertEquals("mobile_data_on", (next as Reply.Confirm).fix.id)
        assertNull(triage.next("no_internet", 1.0, fineDeviceState))
    }
}
