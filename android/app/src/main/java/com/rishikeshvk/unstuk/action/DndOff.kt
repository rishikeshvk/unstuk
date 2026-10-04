package com.rishikeshvk.unstuk.action

import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.os.Build
import com.rishikeshvk.unstuk.selector.SettingTarget
import com.rishikeshvk.unstuk.state.DeviceStateReader
import com.rishikeshvk.unstuk.state.awaitState
import com.rishikeshvk.unstuk.trace.Tracer
import kotlin.time.Duration.Companion.seconds

// Not a public constant, but both targets' Settings export it; the public ZEN_MODE_PRIORITY_SETTINGS opens another page.
private const val ZEN_MODE_SETTINGS = "android.settings.ZEN_MODE_SETTINGS"
private val STATE_TIMEOUT = 5.seconds

/**
 * On Android 15+ `setInterruptionFilter` only changes the app's own zen rule, so it can't undo DND the user turned
 * on; there the accessibility rung is the first rung. Older phones keep the direct call.
 */
class DndOff(
    private val context: Context,
    private val reader: DeviceStateReader,
    private val rung: AccessibilityRung
) {
    private val notifications = context.getSystemService(NotificationManager::class.java)

    suspend fun run(tracer: Tracer): ActionOutcome {
        val before = reader.read()
        tracer.step("precondition", if (before.dndOn) "on" else "off")
        if (!before.dndOn) return ActionOutcome.NothingToDo

        if (Build.VERSION.SDK_INT <= 34 && notifications.isNotificationPolicyAccessGranted) {
            return verifyOff(directCall(tracer), reader, { it.dndOn }, tracer)
        }
        tracer.step("direct_api", "unavailable")
        if (before.keyguardLocked) return ActionOutcome.NeedsUnlock
        val outcome = rung.switchOff(SettingTarget.DND, Intent(ZEN_MODE_SETTINGS), {
            it.dndOn
        }, tracer)
        return verifyOff(outcome, reader, { it.dndOn }, tracer)
    }

    private suspend fun directCall(tracer: Tracer): ActionOutcome {
        notifications.setInterruptionFilter(NotificationManager.INTERRUPTION_FILTER_ALL)
        tracer.step("direct_api", "called")
        val changed = awaitState(context, reader, STATE_TIMEOUT) { !it.dndOn }
        tracer.step("wait_state", if (changed != null) "changed" else "timeout")
        return if (changed !=
            null
        ) {
            ActionOutcome.Verified
        } else {
            ActionOutcome.Failed("State did not change in time")
        }
    }
}
