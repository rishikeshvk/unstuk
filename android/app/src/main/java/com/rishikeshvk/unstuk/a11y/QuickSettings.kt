package com.rishikeshvk.unstuk.a11y

import android.accessibilityservice.AccessibilityService
import android.os.Build
import android.view.accessibility.AccessibilityNodeInfo.AccessibilityAction
import com.rishikeshvk.unstuk.selector.QuickSettingsSelectors
import com.rishikeshvk.unstuk.selector.SettingTarget
import com.rishikeshvk.unstuk.trace.Tracer
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds
import kotlinx.coroutines.delay

// The first shade open after SystemUI rebuilds its tiles took over 2 s on the emulator; found pagers return early.
private val OPEN_TIMEOUT = 5.seconds
private val PAGE_SETTLE = 600.milliseconds

private const val MAX_PAGES = 8

class QuickSettings(
    private val service: AccessibilityService,
    private val selectors: QuickSettingsSelectors,
    private val finder: NodeFinder
) {
    /** Opens the shade and pages through it; traces whether a pager appeared and how many pages were scanned. */
    suspend fun findTile(target: SettingTarget, tracer: Tracer): NodeMatch? {
        val tile = selectors.tiles.getValue(target)
        val pkg = selectors.packageName
        service.performGlobalAction(AccessibilityService.GLOBAL_ACTION_QUICK_SETTINGS)
        if (finder.await(OPEN_TIMEOUT) { findScrollable(pkg, selectors.pagerIds) } == null) {
            tracer.step("open_shade", "no_pager")
            return finder.await(PAGE_SETTLE) { find(pkg, tile) }
        }
        tracer.step("open_shade", "pager")
        // The shade may have been left open on a later page; start from the first so no page is skipped.
        var rewound = 0
        while (rewound < MAX_PAGES &&
            scrollPager(AccessibilityAction.ACTION_SCROLL_BACKWARD)
        ) {
            rewound++
        }
        for (page in 1..MAX_PAGES) {
            finder.await(PAGE_SETTLE) { find(pkg, tile) }?.let { return it }
            if (!scrollPager(AccessibilityAction.ACTION_SCROLL_FORWARD)) {
                tracer.step("scan_pages", "exhausted", detail = "pages=$page rewound=$rewound")
                return null
            }
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
