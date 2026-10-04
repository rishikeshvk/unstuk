package com.rishikeshvk.unstuk.a11y

import android.accessibilityservice.AccessibilityService
import android.content.Intent
import android.view.accessibility.AccessibilityNodeInfo
import com.rishikeshvk.unstuk.selector.SettingTarget
import com.rishikeshvk.unstuk.selector.SettingsSelectors
import com.rishikeshvk.unstuk.trace.Tracer
import kotlin.time.Duration.Companion.seconds

// A cold Settings start while the shade is still closing took ~3 s on the emulator.
private val SCREEN_TIMEOUT = 6.seconds

/** The fallback when no tile is found: opens the target's Settings screen and taps its path. Still the service taps. */
class SettingsScreen(
    private val service: AccessibilityService,
    private val selectors: SettingsSelectors,
    private val finder: NodeFinder
) {
    /** Returns true when every node on the path was found and accepted the click. */
    suspend fun tapPath(target: SettingTarget, screen: Intent, tracer: Tracer): Boolean {
        service.startActivity(
            screen.addFlags(
                Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            )
        )
        tracer.step("open_settings", "started")
        for ((index, selector) in selectors.paths.getValue(target).withIndex()) {
            val match = finder.await(SCREEN_TIMEOUT) { find(selectors.packageName, selector) }
            if (match == null) {
                tracer.step("find_settings_node_$index", "not_found")
                return false
            }
            val clicked = match.node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
            tracer.step(
                "find_settings_node_$index",
                if (clicked) "clicked" else "click_rejected",
                match.strategy
            )
            if (!clicked) return false
        }
        return true
    }
}
