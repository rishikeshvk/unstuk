package com.rishikeshvk.unstuk.action

import android.content.Context
import android.content.Intent
import android.view.accessibility.AccessibilityNodeInfo
import com.rishikeshvk.unstuk.a11y.NodeFinder
import com.rishikeshvk.unstuk.a11y.QuickSettings
import com.rishikeshvk.unstuk.a11y.SettingsScreen
import com.rishikeshvk.unstuk.a11y.UnstukService
import com.rishikeshvk.unstuk.selector.Selectors
import com.rishikeshvk.unstuk.selector.SettingTarget
import com.rishikeshvk.unstuk.state.DeviceState
import com.rishikeshvk.unstuk.state.DeviceStateReader
import com.rishikeshvk.unstuk.state.awaitState
import com.rishikeshvk.unstuk.trace.Tracer
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds
import kotlinx.coroutines.delay

private val STATE_TIMEOUT = 5.seconds
private val CLICK_RETRY_DELAY = 300.milliseconds
private const val CLICK_ATTEMPTS = 3

/**
 * Toggles a setting by having the service tap: the Quick Settings tile first, else the Settings screen.
 * The caller has already checked that the setting needs changing and the device is unlocked.
 */
class AccessibilityRung(
    private val context: Context,
    private val reader: DeviceStateReader,
    private val selectors: Selectors
) {
    suspend fun toggle(
        target: SettingTarget,
        settingsScreen: Intent?,
        reached: (DeviceState) -> Boolean,
        tracer: Tracer
    ): ActionOutcome {
        if (reader.read().advancedProtectionOn == true) {
            return ActionOutcome.NeedsGuidance(
                "Advanced Protection blocks accessibility automation"
            )
        }
        val service = UnstukService.connected.value
            ?: return ActionOutcome.NeedsGuidance("Unstuk service is not enabled")
        val finder = NodeFinder(service)

        if (target in selectors.quickSettings.tiles) {
            val quickSettings = QuickSettings(service, selectors.quickSettings, finder)
            val tile = quickSettings.findTile(target, tracer)
            if (tile != null) {
                tracer.step("find_tile", "found", tile.strategy)
                val outcome = clickAndWait(tile.node, target, quickSettings, reached, tracer)
                quickSettings.close()
                tracer.step("close_shade", "done")
                return outcome
            }
            tracer.step("find_tile", "not_found")
            quickSettings.close()
        } else {
            tracer.step("find_tile", "no_tile")
        }

        if (settingsScreen ==
            null
        ) {
            return ActionOutcome.NeedsGuidance("No tile found and no Settings screen")
        }
        val tapped = SettingsScreen(
            service,
            selectors.settings,
            finder
        ).tapPath(target, settingsScreen, tracer)
        if (!tapped) return ActionOutcome.NeedsGuidance("No tile or Settings switch found")
        return waitFor(reached, tracer)
    }

    private suspend fun clickAndWait(
        node: AccessibilityNodeInfo,
        target: SettingTarget,
        quickSettings: QuickSettings,
        reached: (DeviceState) -> Boolean,
        tracer: Tracer
    ): ActionOutcome {
        if (!clickTile(node, { quickSettings.refind(target)?.node }, tracer)) {
            return ActionOutcome.Failed("Tile rejected the click")
        }
        if (!quickSettings.tapDialog(
                target,
                tracer
            )
        ) {
            return ActionOutcome.Failed("Tile dialog not completed")
        }
        return waitFor(reached, tracer)
    }

    // A tile found while the shade is still expanding can be the collapsed header's copy, which goes stale and
    // rejects clicks. A rejected click changed nothing, so looking the tile up again and retrying is safe.
    private suspend fun clickTile(
        first: AccessibilityNodeInfo,
        refind: () -> AccessibilityNodeInfo?,
        tracer: Tracer
    ): Boolean {
        repeat(CLICK_ATTEMPTS) { attempt ->
            val node = if (attempt == 0) {
                first
            } else {
                delay(CLICK_RETRY_DELAY)
                refind() ?: return@repeat
            }
            if (node.performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
                tracer.step("click_tile", "clicked", detail = "attempt=${attempt + 1}")
                return true
            }
        }
        tracer.step("click_tile", "click_rejected", detail = "attempts=$CLICK_ATTEMPTS")
        return false
    }

    private suspend fun waitFor(reached: (DeviceState) -> Boolean, tracer: Tracer): ActionOutcome {
        val changed = awaitState(context, reader, STATE_TIMEOUT, reached)
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
