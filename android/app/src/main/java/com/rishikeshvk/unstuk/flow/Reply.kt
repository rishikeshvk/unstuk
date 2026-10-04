package com.rishikeshvk.unstuk.flow

import com.rishikeshvk.unstuk.catalog.FixEntry
import com.rishikeshvk.unstuk.catalog.IntentEntry
import com.rishikeshvk.unstuk.diagnose.ScanRow

/**
 * What Unstuk says back to a complaint. [traceName] is the stable name in traces and the e2e runner. A [scan]
 * is what the snapshot behind the reply found, so the screen can show what was checked.
 */
sealed interface Reply {
    val traceName: String

    /** Nothing in the complaint matched anything Unstuk can fix. */
    data object Decline : Reply {
        override val traceName = "decline"
    }

    /** More than one issue fits; the user picks. */
    data class Clarify(val intents: List<IntentEntry>) : Reply {
        override val traceName = "clarify"
    }

    /** No cause holds, so the intent's own guide card. */
    data class AllClear(val intent: IntentEntry, val scan: List<ScanRow>) : Reply {
        override val traceName = "all_clear"
    }

    /**
     * The fix's guide steps: it is high risk, it has no automated rung, or no rung could finish it. [stillFound]
     * means the user said they had done it and a fresh read still finds the cause.
     */
    data class Guide(
        val intent: IntentEntry,
        val fix: FixEntry,
        val reason: String?,
        val scan: List<ScanRow>,
        val stillFound: Boolean = false
    ) : Reply {
        override val traceName = "guide"
    }

    data class Confirm(
        val intent: IntentEntry,
        val fix: FixEntry,
        val confidence: Double,
        val scan: List<ScanRow>
    ) : Reply {
        override val traceName = "confirm"
    }

    /** The gate allows running without asking. */
    data class Run(
        val intent: IntentEntry,
        val fix: FixEntry,
        val confidence: Double,
        val scan: List<ScanRow>
    ) : Reply {
        override val traceName = "run"
    }

    /** Verified by a fresh read, which [scan] also comes from. [next] offers the next cause that still holds. */
    data class Fixed(
        val intent: IntentEntry,
        val fix: FixEntry,
        val next: Reply?,
        val scan: List<ScanRow>
    ) : Reply {
        override val traceName = "verified"
    }

    /** The setting was already as it should be when the fix started. */
    data class AlreadyFine(val intent: IntentEntry, val fix: FixEntry) : Reply {
        override val traceName = "nothing_to_do"
    }

    data object NeedsUnlock : Reply {
        override val traceName = "needs_unlock"
    }
}
