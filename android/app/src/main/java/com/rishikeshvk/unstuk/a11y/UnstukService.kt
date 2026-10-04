package com.rishikeshvk.unstuk.a11y

import android.accessibilityservice.AccessibilityService
import android.content.Intent
import android.view.accessibility.AccessibilityEvent
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * The system binds this service; apps can't bind to it themselves. So it publishes itself while it is connected,
 * and actions reach it through [connected].
 */
class UnstukService : AccessibilityService() {
    override fun onServiceConnected() {
        current.value = this
    }

    override fun onUnbind(intent: Intent?): Boolean {
        current.value = null
        return super.onUnbind(intent)
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent) = Unit

    override fun onInterrupt() = Unit

    companion object {
        private val current = MutableStateFlow<UnstukService?>(null)
        val connected: StateFlow<UnstukService?> = current.asStateFlow()
    }
}
