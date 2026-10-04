package com.rishikeshvk.unstuk.a11y

import android.accessibilityservice.AccessibilityService
import android.os.Build
import android.view.accessibility.AccessibilityNodeInfo.AccessibilityAction
import com.rishikeshvk.unstuk.selector.QuickSettingsSelectors
import com.rishikeshvk.unstuk.selector.SettingTarget
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds
import kotlinx.coroutines.delay

private val OPEN_TIMEOUT = 2.seconds
private val PAGE_SETTLE = 600.milliseconds
private const val MAX_PAGES = 8

class QuickSettings(
    private val service: AccessibilityService,
    private val selectors: QuickSettingsSelectors,
    private val finder: NodeFinder
) {
    suspend fun findTile(target: SettingTarget): NodeMatch? {
        val tile = selectors.tiles.getValue(target)
        val pkg = selectors.packageName
        service.performGlobalAction(AccessibilityService.GLOBAL_ACTION_QUICK_SETTINGS)
        if (finder.await(OPEN_TIMEOUT) { findScrollable(pkg, selectors.pagerIds) } == null) {
            return finder.await(PAGE_SETTLE) { find(pkg, tile) }
        }
        // The shade may have been left open on a later page; start from the first so no page is skipped.
        repeat(MAX_PAGES) {
            if (!scrollPager(AccessibilityAction.ACTION_SCROLL_BACKWARD)) return@repeat
        }
        repeat(MAX_PAGES) {
            finder.await(PAGE_SETTLE) { find(pkg, tile) }?.let { return it }
            if (!scrollPager(AccessibilityAction.ACTION_SCROLL_FORWARD)) return null
        }
        return null
    }

    fun close() {
        val action = if (Build.VERSION.SDK_INT >= 31) {
            AccessibilityService.GLOBAL_ACTION_DISMISS_NOTIFICATION_SHADE
        } else {
            AccessibilityService.GLOBAL_ACTION_BACK
        }
        service.performGlobalAction(action)
    }

    private suspend fun scrollPager(action: AccessibilityAction): Boolean {
        val pager = finder.findScrollable(selectors.packageName, selectors.pagerIds) ?: return false
        if (!pager.performAction(action.id)) return false
        delay(PAGE_SETTLE / 2)
        return true
    }
}
