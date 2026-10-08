package com.rishikeshvk.unstuk.flow

import android.app.NotificationManager
import com.rishikeshvk.unstuk.action.ActionOutcome
import com.rishikeshvk.unstuk.catalog.CatalogTestFiles
import com.rishikeshvk.unstuk.decide.IntentChoice
import com.rishikeshvk.unstuk.decide.RiskGate
import com.rishikeshvk.unstuk.state.fineDeviceState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class TriageTest {
    private val gate = CatalogTestFiles.gate
    private val triage = Triage(CatalogTestFiles.catalog, RiskGate(gate))

    // Sure enough not to ask which issue it is, not sure enough to act alone, wherever the lines are tuned.
    private val unsure = (gate.clarifyBelow + gate.automaticAt) / 2

    @Test
    fun `nothing matched declines`() {
        assertTrue(triage.triage(IntentChoice(emptyMap()), fineDeviceState) is Reply.Decline)
    }

    @Test
    fun `out of scope likelier than any intent declines`() {
        val choice = IntentChoice(mapOf("no_internet" to 0.3), outOfScope = 0.7)
        assertTrue(triage.triage(choice, fineDeviceState) is Reply.Decline)
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
            IntentChoice(mapOf("no_internet" to unsure, "wrong_time" to 1 - unsure)),
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

    @Test
    fun `a low-risk fix with nothing to run goes straight to guided steps`() {
        val reply = triage.triage(
            IntentChoice(mapOf("colours_wrong" to 1.0)),
            fineDeviceState.copy(greyscaleOn = true)
        )
        assertEquals("greyscale_off", (reply as Reply.Guide).fix.id)
    }

    @Test
    fun `a diagnosed reply shows every real check, found or fine`() {
        val reply = triage.triage(
            IntentChoice(mapOf("phone_not_ringing" to unsure, "cant_hear_call" to 1 - unsure)),
            fineDeviceState.copy(
                interruptionFilter = NotificationManager.INTERRUPTION_FILTER_PRIORITY
            )
        )
        assertEquals(
            listOf("dnd_off" to true, "ringer_normal" to false, "ring_volume_up" to false),
            (reply as Reply.Confirm).scan.map { it.fix.id to it.holds }
        )
    }

    @Test
    fun `a verified run reports from the fresh read and offers what still holds`() {
        val state = fineDeviceState.copy(online = false, wifiOn = false, mobileDataOn = false)
        val reply = triage.afterRun(
            ActionOutcome.Verified,
            "no_internet",
            "airplane_off",
            1.0,
            state
        )
        reply as Reply.Fixed
        assertEquals("airplane_off", reply.fix.id)
        assertEquals("mobile_data_on", (reply.next as Reply.Confirm).fix.id)
        assertEquals(false, reply.scan.first { it.fix.id == "airplane_off" }.holds)
    }

    @Test
    fun `a run that could not finish falls back to the fix's guide`() {
        val reply = triage.afterRun(
            ActionOutcome.Failed("tile not found"),
            "no_internet",
            "airplane_off",
            1.0,
            fineDeviceState.copy(airplaneModeOn = true)
        )
        assertEquals("tile not found", (reply as Reply.Guide).reason)
        assertTrue(reply.scan.first().holds)
    }

    @Test
    fun `a recheck counts as fixed only when a fresh read no longer finds the cause`() {
        val fixed = triage.recheck("colours_wrong", "greyscale_off", 1.0, fineDeviceState)
        assertEquals("greyscale_off", (fixed as Reply.Fixed).fix.id)

        val still = triage.recheck(
            "colours_wrong",
            "greyscale_off",
            1.0,
            fineDeviceState.copy(greyscaleOn = true)
        )
        assertTrue((still as Reply.Guide).stillFound)
    }
}
