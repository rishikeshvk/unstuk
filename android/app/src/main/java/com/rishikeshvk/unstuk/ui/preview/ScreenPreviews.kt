package com.rishikeshvk.unstuk.ui.preview

import android.content.res.Configuration
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import com.rishikeshvk.unstuk.catalog.Area
import com.rishikeshvk.unstuk.catalog.Cause
import com.rishikeshvk.unstuk.catalog.FixEntry
import com.rishikeshvk.unstuk.catalog.IntentEntry
import com.rishikeshvk.unstuk.catalog.Risk
import com.rishikeshvk.unstuk.catalog.Rung
import com.rishikeshvk.unstuk.diagnose.ScanRow
import com.rishikeshvk.unstuk.flow.FixStep
import com.rishikeshvk.unstuk.flow.Reply
import com.rishikeshvk.unstuk.ui.AccessStatus
import com.rishikeshvk.unstuk.ui.HomeScreen
import com.rishikeshvk.unstuk.ui.SettingsScreen
import com.rishikeshvk.unstuk.ui.reply.ReplyActions
import com.rishikeshvk.unstuk.ui.reply.ReplyScreen
import com.rishikeshvk.unstuk.ui.theme.ThemeChoice
import com.rishikeshvk.unstuk.ui.theme.UnstukTheme

@Preview(name = "Light", showBackground = true, widthDp = 390, heightDp = 844)
@Preview(
    name = "Dark",
    showBackground = true,
    widthDp = 390,
    heightDp = 844,
    uiMode = Configuration.UI_MODE_NIGHT_YES
)
@Preview(
    name = "Large text",
    showBackground = true,
    widthDp = 390,
    heightDp = 844,
    fontScale = 1.3f
)
private annotation class ScreenPreviews

private val dnd = FixEntry(
    id = "dnd_off",
    label = "Turn off Do Not Disturb",
    subject = "Do Not Disturb",
    finding = "Do Not Disturb is on.",
    why = "It silences calls and notifications.",
    done = "Do Not Disturb is off.",
    risk = Risk.LOW,
    rungs = listOf(Rung.DIRECT, Rung.GUIDED),
    guide = listOf(
        "Swipe down twice from the top of the screen.",
        "Tap Do Not Disturb so that it turns grey."
    )
)

private val ringer = dnd.copy(
    id = "ringer_normal",
    label = "Switch the ringer from silent or vibrate to ring",
    subject = "Ringer",
    finding = "The ringer is on silent or vibrate.",
    why = "Calls buzz or stay quiet instead of ringing.",
    done = "The ringer is set to ring."
)

private val notRinging = IntentEntry(
    id = "phone_not_ringing",
    option = "The phone does not ring when someone calls",
    area = Area.CALLS,
    causes = listOf(Cause("dnd_on", "dnd_off"), Cause("ringer_not_normal", "ringer_normal")),
    fallback = listOf("Ask someone to call you, and press the volume-up button while it rings.")
)

private val noActions = ReplyActions(
    back = {},
    finish = {},
    updateComplaint = {},
    submit = {},
    openTopic = {},
    pick = {},
    noneOfThese = {},
    confirm = { _, _, _ -> },
    retry = {},
    recheck = {},
    showTips = {},
    showReply = {}
)

@Composable
private fun Framed(content: @Composable () -> Unit) {
    UnstukTheme { Surface(color = MaterialTheme.colorScheme.background) { content() } }
}

@ScreenPreviews
@Composable
private fun HomePreview() = Framed {
    HomeScreen(
        complaint = "",
        onComplaintChange = {},
        onSubmit = {},
        onTopic = {},
        onAccess = {},
        onSettings = {},
        showBanner = true,
        accessMissing = true,
        onDismissBanner = {}
    )
}

@ScreenPreviews
@Composable
private fun ConfirmPreview() = Framed {
    val scan = listOf(ScanRow(dnd, holds = true), ScanRow(ringer, holds = true))
    ReplyScreen(
        Reply.Confirm(notRinging, dnd, 0.7, scan),
        "phone doesn't ring",
        emptySet(),
        emptyList(),
        noActions
    )
}

@ScreenPreviews
@Composable
private fun FixedPreview() = Framed {
    val scan = listOf(ScanRow(dnd, holds = false), ScanRow(ringer, holds = false))
    val steps =
        listOf(FixStep(Rung.DIRECT, ok = true, millis = 14), FixStep(null, ok = true, millis = 6))
    ReplyScreen(
        Reply.Fixed(notRinging, ringer, next = null, scan),
        "",
        setOf("dnd_off", "ringer_normal"),
        steps,
        noActions
    )
}

@ScreenPreviews
@Composable
private fun GuidePreview() = Framed {
    val reply = Reply.Guide(
        notRinging,
        dnd,
        reason = "tile not found",
        scan = listOf(ScanRow(dnd, holds = true))
    )
    ReplyScreen(reply, "", emptySet(), emptyList(), noActions)
}

@ScreenPreviews
@Composable
private fun SettingsPreview() = Framed {
    SettingsScreen(
        theme = ThemeChoice.SYSTEM,
        onTheme = {},
        access = AccessStatus(service = true, policy = false, writeSettings = false),
        onAccess = {},
        onBack = {},
        onDebug = {}
    )
}
