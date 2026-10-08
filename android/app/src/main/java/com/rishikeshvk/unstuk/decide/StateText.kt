package com.rishikeshvk.unstuk.decide

import com.rishikeshvk.unstuk.catalog.Catalog
import com.rishikeshvk.unstuk.diagnose.Checks
import com.rishikeshvk.unstuk.state.DeviceState

/**
 * The device state as the model reads it, as `training_examples.render_state` wrote it: the finding of each of
 * [checks] that holds, in that order, joined by spaces. Empty when none holds, so the complaint is read alone.
 */
class StateText(catalog: Catalog, private val checks: List<String>) {
    private val findings = catalog.intents.flatMap { it.causes }
        .associate { it.check to catalog.fix(it.fix).finding }

    fun render(state: DeviceState): String = checks
        .filter { Checks.all.getValue(it)(state) }
        .joinToString(" ") { findings.getValue(it) }
}
