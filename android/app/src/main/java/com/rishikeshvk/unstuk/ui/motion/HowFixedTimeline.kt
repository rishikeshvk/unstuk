package com.rishikeshvk.unstuk.ui.motion

import androidx.annotation.StringRes
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
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
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.catalog.Rung
import com.rishikeshvk.unstuk.flow.FixStep

/**
 * "How I fixed it": the executor ladder of the last run, read back from its on-device trace. Collapsed by
 * default, so it costs a user nothing and shows anyone curious the system underneath.
 */
@Composable
fun HowFixedTimeline(steps: List<FixStep>, modifier: Modifier = Modifier) {
    if (steps.isEmpty()) return
    var open by rememberSaveable { mutableStateOf(false) }
    val chevron by animateFloatAsState(if (open) 180f else 0f, label = "chevron")
    val dash = MaterialTheme.colorScheme.outline
    Column(
        modifier
            .fillMaxWidth()
            .drawBehind {
                drawRoundRect(
                    color = dash,
                    cornerRadius = CornerRadius(24.dp.toPx()),
                    style = Stroke(
                        width = 2.dp.toPx(),
                        pathEffect = PathEffect.dashPathEffect(floatArrayOf(10f, 8f))
                    )
                )
            }
            .padding(horizontal = 18.dp, vertical = 6.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = 48.dp)
                .toggleable(value = open, role = Role.Switch, onValueChange = { open = it }),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                stringResource(R.string.how_fixed),
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.weight(1f)
            )
            Icon(
                painterResource(R.drawable.ic_chevron_down),
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier
                    .size(20.dp)
                    .rotate(chevron)
            )
        }
        AnimatedVisibility(
            visible = open,
            enter = expandVertically() + fadeIn(),
            exit = shrinkVertically() + fadeOut()
        ) {
            Column(
                Modifier.padding(bottom = 12.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                steps.forEachIndexed { index, step ->
                    StepLine(step, last = index == steps.lastIndex)
                }
            }
        }
    }
}

@Composable
private fun StepLine(step: FixStep, last: Boolean) {
    val colors = MaterialTheme.colorScheme
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        val dot = Modifier.size(10.dp)
        Box(
            when {
                !step.ok -> dot.border(2.dp, colors.outline, CircleShape)
                last -> dot.background(colors.tertiary, CircleShape)
                else -> dot.background(colors.onSurface, CircleShape)
            }
        )
        Text(
            stringResource(labelFor(step)),
            style = MaterialTheme.typography.bodySmall,
            color = if (step.ok) colors.onSurface else colors.onSurfaceVariant,
            modifier = Modifier.weight(1f)
        )
        if (step.ok) {
            Text(
                stringResource(R.string.step_millis, step.millis),
                style = MaterialTheme.typography.bodySmall,
                color = colors.onSurfaceVariant
            )
        }
    }
}

@StringRes
private fun labelFor(step: FixStep): Int = when (step.rung) {
    null -> if (step.ok) R.string.step_verify_ok else R.string.step_verify_no
    Rung.DIRECT -> if (step.ok) R.string.step_direct_ok else R.string.step_direct_no
    Rung.PANEL -> if (step.ok) R.string.step_panel_ok else R.string.step_panel_no
    Rung.ACCESSIBILITY ->
        if (step.ok) R.string.step_accessibility_ok else R.string.step_accessibility_no
    Rung.GUIDED -> error("Guided steps end the ladder and are never traced as a rung")
}
