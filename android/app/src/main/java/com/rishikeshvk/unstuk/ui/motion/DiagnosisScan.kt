package com.rishikeshvk.unstuk.ui.motion

import androidx.annotation.DrawableRes
import androidx.annotation.StringRes
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.slideInVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.diagnose.ScanRow
import kotlinx.coroutines.delay

private const val STAGGER_MS = 150L

private enum class RowStatus(@StringRes val label: Int, @DrawableRes val icon: Int) {
    FOUND(R.string.scan_found, R.drawable.ic_alert),
    FIXED(R.string.scan_fixed, R.drawable.ic_check),
    FINE(R.string.scan_fine, R.drawable.ic_check)
}

/**
 * What the snapshot behind a reply checked, one row per real check, revealed one after another. Every row is a
 * real check result; only its entrance is animated. [fixed] are fixes verified earlier in this conversation.
 */
@Composable
fun DiagnosisScan(rows: List<ScanRow>, fixed: Set<String>, modifier: Modifier = Modifier) {
    if (rows.isEmpty()) return
    val reduced = rememberReducedMotion()
    var revealed by remember(rows) { mutableIntStateOf(if (reduced) rows.size else 0) }
    LaunchedEffect(rows) {
        while (revealed < rows.size) {
            revealed++
            delay(STAGGER_MS)
        }
    }
    Column(
        modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surface, MaterialTheme.shapes.large)
            .padding(horizontal = 18.dp, vertical = 14.dp)
    ) {
        Text(
            stringResource(R.string.scan_title),
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier
                .padding(bottom = 4.dp)
                .semantics { heading() }
        )
        rows.forEachIndexed { index, row ->
            val status = when {
                row.holds -> RowStatus.FOUND
                row.fix.id in fixed -> RowStatus.FIXED
                else -> RowStatus.FINE
            }
            AnimatedVisibility(
                visible = index < revealed,
                enter = fadeIn() + slideInVertically { it / 3 }
            ) {
                ScanLine(row.fix.subject, status)
            }
        }
    }
}

@Composable
private fun ScanLine(subject: String, status: RowStatus) {
    val label = stringResource(status.label)
    val description = stringResource(R.string.scan_row, subject, label)
    val accent = status != RowStatus.FINE
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 44.dp)
            .clearAndSetSemantics { contentDescription = description },
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        StatusDot(status.icon, accent)
        Text(
            subject,
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.weight(1f)
        )
        Text(
            label,
            style = MaterialTheme.typography.bodySmall,
            fontWeight = if (accent) FontWeight.SemiBold else FontWeight.Normal,
            color = if (accent) {
                MaterialTheme.colorScheme.onTertiaryContainer
            } else {
                MaterialTheme.colorScheme.onSurfaceVariant
            }
        )
    }
}

@Composable
private fun StatusDot(@DrawableRes icon: Int, accent: Boolean) {
    val colors = MaterialTheme.colorScheme
    val base = Modifier.size(28.dp)
    Box(
        modifier = if (accent) {
            base.background(colors.tertiary, CircleShape)
        } else {
            base.border(2.dp, colors.outline, CircleShape)
        },
        contentAlignment = Alignment.Center
    ) {
        Icon(
            painterResource(icon),
            contentDescription = null,
            tint = if (accent) colors.onTertiary else colors.onSurfaceVariant,
            modifier = Modifier.size(if (accent) 16.dp else 14.dp)
        )
    }
}
