package com.rishikeshvk.unstuk.ui.reply

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.catalog.FixEntry
import com.rishikeshvk.unstuk.catalog.Rung
import com.rishikeshvk.unstuk.fix.RungForecast
import com.rishikeshvk.unstuk.ui.components.HintRow

/**
 * What the user will see happen, said before it happens: the screen moving by itself (accessibility), or a
 * Settings screen where they make the change (panel). A direct change needs no warning, so it shows nothing.
 */
@Composable
fun RungHint(fix: FixEntry, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val rung = remember(fix) { RungForecast(context).firstActing(fix) }
    val colors = MaterialTheme.colorScheme
    val card = modifier
        .fillMaxWidth()
        .background(colors.surface, MaterialTheme.shapes.medium)
        .padding(horizontal = 12.dp, vertical = 8.dp)
    when (rung) {
        Rung.ACCESSIBILITY -> HintRow(
            R.drawable.ic_hand,
            stringResource(R.string.hint_accessibility),
            card
        )
        Rung.PANEL -> Column(card, verticalArrangement = Arrangement.spacedBy(4.dp)) {
            HintRow(
                R.drawable.ic_phone,
                stringResource(R.string.hint_panel_open),
                wellColor = colors.background
            )
            HintRow(
                R.drawable.ic_tap,
                stringResource(R.string.hint_panel_tap),
                iconTint = colors.onTertiaryContainer,
                wellColor = colors.tertiaryContainer
            )
            HintRow(
                R.drawable.ic_check,
                stringResource(R.string.hint_panel_check),
                wellColor = colors.background
            )
        }
        Rung.DIRECT, Rung.GUIDED -> Unit
    }
}
