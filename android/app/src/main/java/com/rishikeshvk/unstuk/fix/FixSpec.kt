package com.rishikeshvk.unstuk.fix

import com.rishikeshvk.unstuk.catalog.Rung
import com.rishikeshvk.unstuk.selector.SettingTarget
import com.rishikeshvk.unstuk.state.DeviceState

/**
 * How the executor performs one catalog fix. Each non-null field is one rung of the ladder; guided steps come
 * from the catalog and are always last.
 */
class FixSpec(
    /** Whether the fix has taken effect, judged from the state before it ran and a fresh read. */
    val reached: (before: DeviceState, now: DeviceState) -> Boolean,
    val direct: DirectChange? = null,
    /** A Settings Panel or screen the app opens for the user to tap. */
    val panelAction: String? = null,
    /** The tile or switch our service taps; it toggles, so the runner only taps when [reached] is false. */
    val accessibility: SettingTarget? = null,
    /** The screen the accessibility rung falls back to, and the one the guide card's button opens. */
    val settingsAction: String? = null
) {
    val rungs: List<Rung>
        get() = listOfNotNull(
            direct?.let { Rung.DIRECT },
            panelAction?.let { Rung.PANEL },
            accessibility?.let { Rung.ACCESSIBILITY }
        ) + Rung.GUIDED
}
