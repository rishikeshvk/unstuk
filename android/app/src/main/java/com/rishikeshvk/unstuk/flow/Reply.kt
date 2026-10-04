package com.rishikeshvk.unstuk.flow

import com.rishikeshvk.unstuk.catalog.FixEntry
import com.rishikeshvk.unstuk.catalog.IntentEntry

/** What Unstuk says back to a complaint. [traceName] is the stable name in traces and the e2e runner. */
sealed interface Reply {
    val traceName: String

    /** Nothing in the complaint matched anything Unstuk can fix. */
    data class Decline(val options: List<String>) : Reply {
        override val traceName = "decline"
    }

    /** More than one issue fits; the user picks. */
    data class Clarify(val intents: List<IntentEntry>) : Reply {
        override val traceName = "clarify"
    }

    /** No cause holds, so the intent's own guide card. */
    data class AllClear(val intent: IntentEntry) : Reply {
        override val traceName = "all_clear"
    }

    /** The fix's guide steps: it is high risk, or no rung could finish it. */
    data class Guide(val fix: FixEntry, val reason: String?) : Reply {
        override val traceName = "guide"
    }

    data class Confirm(val intent: IntentEntry, val fix: FixEntry, val confidence: Double) : Reply {
        override val traceName = "confirm"
    }

    /** The gate allows running without asking. */
    data class Run(val intent: IntentEntry, val fix: FixEntry, val confidence: Double) : Reply {
        override val traceName = "run"
    }

    /** Verified by a fresh read. [next] offers the next cause that still holds, if any. */
    data class Fixed(val fix: FixEntry, val next: Reply?) : Reply {
        override val traceName = "verified"
    }

    /** The setting was already as it should be when the fix started. */
    data class AlreadyFine(val fix: FixEntry) : Reply {
        override val traceName = "nothing_to_do"
    }

    data object NeedsUnlock : Reply {
        override val traceName = "needs_unlock"
    }
}
