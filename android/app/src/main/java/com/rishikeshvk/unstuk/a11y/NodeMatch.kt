package com.rishikeshvk.unstuk.a11y

import android.view.accessibility.AccessibilityNodeInfo

/** A clickable node and the strategy that found it, recorded in the trace. */
data class NodeMatch(val node: AccessibilityNodeInfo, val strategy: String)
