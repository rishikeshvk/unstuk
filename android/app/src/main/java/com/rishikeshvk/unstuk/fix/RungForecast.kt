package com.rishikeshvk.unstuk.fix

import android.content.Context
import android.os.Build
import com.rishikeshvk.unstuk.a11y.UnstukService
import com.rishikeshvk.unstuk.catalog.FixEntry
import com.rishikeshvk.unstuk.catalog.Rung

/**
 * The first rung a run of a fix is expected to act on, by the same SDK, grant and service rules the ladder uses,
 * so a screen can say beforehand what will happen. A forecast only: the run itself still decides.
 */
class RungForecast(private val context: Context) {
    fun firstActing(fix: FixEntry): Rung {
        val spec = FixSpecs.get(fix.id)
        return fix.rungs.first { rung ->
            when (rung) {
                Rung.DIRECT -> spec.direct?.let(::isAvailable) == true
                Rung.ACCESSIBILITY -> UnstukService.connected.value != null
                Rung.PANEL, Rung.GUIDED -> true
            }
        }
    }

    private fun isAvailable(change: DirectChange) =
        Build.VERSION.SDK_INT <= change.maxSdk && change.grant?.isGranted(context) != false
}
