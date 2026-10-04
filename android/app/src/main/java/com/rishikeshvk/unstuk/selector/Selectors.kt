package com.rishikeshvk.unstuk.selector

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** A setting the executor can switch off. Serial names are the keys used in the selector files. */
@Serializable
enum class SettingTarget {
    @SerialName("airplane_mode")
    AIRPLANE_MODE,

    @SerialName("dnd")
    DND
}

/**
 * Finds one node: by a resource-id unique to it, else by a label variant. When [labelIds] is set, a label only
 * counts on a node with one of those ids, because the same words also appear in summaries and status icons.
 */
@Serializable
data class NodeSelector(
    val resourceIds: List<String> = emptyList(),
    val labelIds: List<String> = emptyList(),
    val labels: List<String> = emptyList()
)

@Serializable
data class QuickSettingsSelectors(
    val packageName: String,
    val pagerIds: List<String>,
    val tiles: Map<SettingTarget, NodeSelector>
)

/** Each path is the nodes to tap in order after opening the target's Settings screen. */
@Serializable
data class SettingsSelectors(
    val packageName: String,
    val paths: Map<SettingTarget, List<NodeSelector>>
)

@Serializable
data class Selectors(val quickSettings: QuickSettingsSelectors, val settings: SettingsSelectors)
