package com.rishikeshvk.unstuk.debug

import android.accessibilityservice.AccessibilityService
import android.content.Intent
import android.view.accessibility.AccessibilityNodeInfo
import android.view.accessibility.AccessibilityNodeInfo.AccessibilityAction
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds
import kotlinx.coroutines.delay
import kotlinx.serialization.Serializable

private val OPEN_WAIT = 2.seconds
private val PAGE_SETTLE = 700.milliseconds
private const val MAX_PAGES = 10

@Serializable
data class DumpedNode(
    val page: Int,
    val text: String?,
    val description: String?,
    val id: String?,
    val clickable: Boolean,
    val checkable: Boolean
)

/** Reads every labelled node on a screen, page by page, for the node-label test set (M3 step 10). */
class ScreenLabels(private val service: AccessibilityService) {
    suspend fun quickSettings(packageName: String, pagerIds: List<String>): List<DumpedNode> {
        service.performGlobalAction(AccessibilityService.GLOBAL_ACTION_QUICK_SETTINGS)
        delay(OPEN_WAIT)
        // Start from the first page, in case the shade was left on a later one.
        var rewound = 0
        while (rewound < MAX_PAGES &&
            scroll(packageName, pagerIds, AccessibilityAction.ACTION_SCROLL_BACKWARD)
        ) {
            rewound++
        }
        return pages(packageName, pagerIds)
    }

    suspend fun settings(packageName: String, action: String): List<DumpedNode> {
        service.startActivity(Intent(action).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        delay(OPEN_WAIT)
        val nodes = pages(packageName, emptyList())
        service.performGlobalAction(AccessibilityService.GLOBAL_ACTION_HOME)
        return nodes
    }

    private suspend fun pages(packageName: String, scrollIds: List<String>): List<DumpedNode> {
        val nodes = mutableListOf<DumpedNode>()
        for (page in 1..MAX_PAGES) {
            nodes += visible(packageName, page)
            if (!scroll(packageName, scrollIds, AccessibilityAction.ACTION_SCROLL_FORWARD)) break
        }
        return nodes.distinctBy { Triple(it.text, it.description, it.id) }
    }

    private fun visible(packageName: String, page: Int): List<DumpedNode> = roots(packageName)
        .flatMap { descendants(it) }
        .filter {
            it.isVisibleToUser &&
                (!it.text.isNullOrBlank() || !it.contentDescription.isNullOrBlank())
        }
        .map {
            DumpedNode(
                page = page,
                text = it.text?.toString(),
                description = it.contentDescription?.toString(),
                id = it.viewIdResourceName,
                clickable = it.isClickable,
                checkable = it.isCheckable
            )
        }

    private suspend fun scroll(
        packageName: String,
        ids: List<String>,
        action: AccessibilityAction
    ): Boolean {
        val scrollable = if (ids.isEmpty()) {
            roots(packageName).flatMap { descendants(it) }.firstOrNull {
                it.isScrollable &&
                    it.isVisibleToUser
            }
        } else {
            roots(packageName)
                .flatMap { root -> ids.flatMap { root.findAccessibilityNodeInfosByViewId(it) } }
                .firstOrNull { it.isScrollable && it.isVisibleToUser }
        }
        if (scrollable?.performAction(action.id) != true) return false
        delay(PAGE_SETTLE)
        return true
    }

    private fun roots(packageName: String): List<AccessibilityNodeInfo> =
        service.windows.mapNotNull { it.root }.filter { it.packageName == packageName }

    private fun descendants(root: AccessibilityNodeInfo): List<AccessibilityNodeInfo> {
        val found = mutableListOf<AccessibilityNodeInfo>()
        val queue = ArrayDeque(listOf(root))
        while (queue.isNotEmpty()) {
            val node = queue.removeFirst()
            found += node
            for (i in 0 until node.childCount) node.getChild(i)?.let(queue::addLast)
        }
        return found
    }
}
