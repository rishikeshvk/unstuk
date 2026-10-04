package com.rishikeshvk.unstuk.a11y

import android.accessibilityservice.AccessibilityService
import android.view.accessibility.AccessibilityNodeInfo
import com.rishikeshvk.unstuk.selector.NodeSelector
import com.rishikeshvk.unstuk.selector.matchesLabel
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.TimeSource
import kotlinx.coroutines.delay

private val POLL_INTERVAL = 100.milliseconds

/** Finds visible nodes in the windows of one package, so labels in other apps (or our own UI) never match. */
class NodeFinder(private val service: AccessibilityService) {
    fun find(packageName: String, selector: NodeSelector): NodeMatch? {
        val roots = roots(packageName)
        return roots.firstNotNullOfOrNull { byResourceId(it, selector) }
            ?: roots.firstNotNullOfOrNull { byLabel(it, selector) }
    }

    fun findScrollable(packageName: String, ids: List<String>): AccessibilityNodeInfo? =
        roots(packageName)
            .flatMap { root -> ids.flatMap { root.findAccessibilityNodeInfosByViewId(it) } }
            .firstOrNull { it.isScrollable && it.isVisibleToUser }

    // UI appears asynchronously and emits no single "ready" event, so poll the tree the way UiAutomator does.
    suspend fun <T : Any> await(timeout: Duration, lookup: NodeFinder.() -> T?): T? {
        val deadline = TimeSource.Monotonic.markNow() + timeout
        while (true) {
            lookup()?.let { return it }
            if (deadline.hasPassedNow()) return null
            delay(POLL_INTERVAL)
        }
    }

    private fun roots(packageName: String) =
        service.windows.mapNotNull { it.root }.filter { it.packageName == packageName }

    private fun byResourceId(root: AccessibilityNodeInfo, selector: NodeSelector) =
        selector.resourceIds
            .asSequence()
            .flatMap { root.findAccessibilityNodeInfosByViewId(it) }
            .filter { it.isVisibleToUser }
            .firstNotNullOfOrNull { clickableSelfOrAncestor(it) }
            ?.let { NodeMatch(it, "resource-id") }

    private fun byLabel(root: AccessibilityNodeInfo, selector: NodeSelector) = descendants(root)
        .filter { it.isVisibleToUser && hasLabel(it, selector) }
        .firstNotNullOfOrNull { clickableSelfOrAncestor(it) }
        ?.let { NodeMatch(it, "label") }

    private fun hasLabel(node: AccessibilityNodeInfo, selector: NodeSelector): Boolean {
        if (selector.labelIds.isNotEmpty() &&
            node.viewIdResourceName !in selector.labelIds
        ) {
            return false
        }
        return matchesLabel(node.text, selector.labels) ||
            matchesLabel(node.contentDescription, selector.labels)
    }

    private fun descendants(root: AccessibilityNodeInfo): Sequence<AccessibilityNodeInfo> =
        sequence {
            val queue = ArrayDeque(listOf(root))
            while (queue.isNotEmpty()) {
                val node = queue.removeFirst()
                yield(node)
                for (i in 0 until node.childCount) node.getChild(i)?.let(queue::addLast)
            }
        }

    // Status-bar icons repeat tile labels but have no clickable ancestor, so they drop out here.
    private fun clickableSelfOrAncestor(node: AccessibilityNodeInfo): AccessibilityNodeInfo? =
        generateSequence(node) { it.parent }.firstOrNull { it.isClickable }
}
