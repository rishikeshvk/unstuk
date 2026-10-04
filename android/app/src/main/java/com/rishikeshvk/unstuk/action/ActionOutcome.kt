package com.rishikeshvk.unstuk.action

/** How an action ended. Only [Verified] is a success, and only after a fresh state read agreed. */
sealed interface ActionOutcome {
    val traceName: String

    data object Verified : ActionOutcome {
        override val traceName = "verified"
    }

    data object NothingToDo : ActionOutcome {
        override val traceName = "nothing_to_do"
    }

    data object NeedsUnlock : ActionOutcome {
        override val traceName = "needs_unlock"
    }

    data class NeedsGuidance(val reason: String) : ActionOutcome {
        override val traceName = "needs_guidance"
    }

    data class Failed(val reason: String) : ActionOutcome {
        override val traceName = "failed"
    }
}
