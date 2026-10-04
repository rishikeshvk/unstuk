package com.rishikeshvk.unstuk.diagnose

import com.rishikeshvk.unstuk.catalog.Catalog
import com.rishikeshvk.unstuk.catalog.FixEntry
import com.rishikeshvk.unstuk.state.DeviceState

/** Picks the first cause of an intent, in catalog order, that holds on a snapshot. */
class Diagnoser(private val catalog: Catalog) {
    /** The fix for the first cause that holds, or null when everything Unstuk can check looks fine. */
    fun diagnose(intentId: String, state: DeviceState): FixEntry? = catalog.intent(intentId).causes
        .firstOrNull { Checks.all.getValue(it.check)(state) }
        ?.let { catalog.fix(it.fix) }
}
