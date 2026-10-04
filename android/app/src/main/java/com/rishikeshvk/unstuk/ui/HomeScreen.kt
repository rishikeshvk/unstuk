package com.rishikeshvk.unstuk.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.catalog.Area
import com.rishikeshvk.unstuk.ui.components.ComplaintField
import com.rishikeshvk.unstuk.ui.components.HomeTopBar
import com.rishikeshvk.unstuk.ui.components.PrimaryButton
import com.rishikeshvk.unstuk.ui.components.TopicTile
import com.rishikeshvk.unstuk.ui.motion.ScallopShape
import com.rishikeshvk.unstuk.ui.motion.UnknotMark
import com.rishikeshvk.unstuk.ui.motion.UnknotMotion
import com.rishikeshvk.unstuk.ui.motion.rememberReducedMotion

// From this font scale the topic grid has room for one tile per row only.
private const val LARGE_TEXT = 1.3f
private const val BLOB_TURN_MS = 40_000

/** The one question, a field to answer it, and topics for those who would rather tap. */
@Composable
fun HomeScreen(
    complaint: String,
    onComplaintChange: (String) -> Unit,
    onSubmit: () -> Unit,
    onTopic: (Area) -> Unit,
    onAccess: () -> Unit,
    showBanner: Boolean,
    accessMissing: Boolean,
    onDismissBanner: () -> Unit,
    modifier: Modifier = Modifier,
    tileModifier: @Composable (Area) -> Modifier = { Modifier }
) {
    Box(modifier.fillMaxSize()) {
        Blob(Modifier.align(Alignment.TopEnd))
        Column(Modifier.verticalScroll(rememberScrollState())) {
            HomeTopBar(onAccess, accessMissing)
            AnimatedVisibility(showBanner) {
                AccessBanner(onSetUp = onAccess, onDismiss = onDismissBanner)
            }
            Column(
                Modifier.padding(horizontal = 20.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Spacer(Modifier.height(18.dp))
                Text(
                    stringResource(R.string.home_title),
                    style = MaterialTheme.typography.displaySmall,
                    modifier = Modifier
                        .widthIn(max = 320.dp)
                        .semantics { heading() }
                )
                Text(
                    stringResource(R.string.home_subtitle),
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(Modifier.height(10.dp))
                ComplaintField(complaint, onComplaintChange, onSubmit)
                PrimaryButton(
                    stringResource(R.string.home_submit),
                    onClick = onSubmit,
                    enabled = complaint.isNotBlank(),
                    trailingIcon = R.drawable.ic_forward
                )
                Spacer(Modifier.height(18.dp))
                Text(
                    stringResource(R.string.home_topics),
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.semantics { heading() }
                )
                TopicGrid(onTopic, tileModifier)
                Spacer(Modifier.height(20.dp))
            }
        }
    }
}

@Composable
private fun TopicGrid(onTopic: (Area) -> Unit, tileModifier: @Composable (Area) -> Modifier) {
    val perRow = if (LocalDensity.current.fontScale >= LARGE_TEXT) 1 else 2
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Area.entries.chunked(perRow).forEach { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                row.forEach { area ->
                    TopicTile(
                        area,
                        onClick = { onTopic(area) },
                        modifier = Modifier
                            .weight(1f)
                            .then(tileModifier(area))
                    )
                }
            }
        }
    }
}

@Composable
private fun AccessBanner(onSetUp: () -> Unit, onDismiss: () -> Unit) {
    Column(
        Modifier
            .padding(horizontal = 20.dp, vertical = 8.dp)
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.tertiaryContainer, MaterialTheme.shapes.large)
            .padding(start = 16.dp, top = 6.dp, bottom = 14.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Row(verticalAlignment = Alignment.Top) {
            Column(
                Modifier
                    .weight(1f)
                    .padding(top = 10.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Text(
                    stringResource(R.string.banner_title),
                    style = MaterialTheme.typography.titleMedium
                )
                Text(
                    stringResource(R.string.banner_body),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            IconButton(onClick = onDismiss) {
                Icon(
                    painterResource(R.drawable.ic_close),
                    contentDescription = stringResource(R.string.banner_dismiss),
                    modifier = Modifier.size(18.dp)
                )
            }
        }
        PrimaryButton(
            stringResource(R.string.banner_action),
            onClick = onSetUp,
            modifier = Modifier
                .padding(end = 16.dp)
                .height(48.dp)
        )
    }
}

/** The slowly turning tangerine cookie behind the question, with the logo line inside: the brand's signature. */
@Composable
private fun Blob(modifier: Modifier) {
    val reduced = rememberReducedMotion()
    val angle by rememberInfiniteTransition(label = "blob").animateFloat(
        initialValue = 0f,
        targetValue = if (reduced) 0f else 360f,
        animationSpec = infiniteRepeatable(tween(BLOB_TURN_MS, easing = LinearEasing)),
        label = "angle"
    )
    Box(
        modifier
            .offset(x = 86.dp, y = 40.dp)
            .size(260.dp)
            .rotate(angle)
            .background(MaterialTheme.colorScheme.tertiaryContainer, ScallopShape.Cookie)
    ) {
        UnknotMark(
            UnknotMotion.STILL,
            MaterialTheme.colorScheme.tertiary.copy(alpha = 0.35f),
            Modifier
                .padding(70.dp)
                .fillMaxSize()
                .rotate(-angle),
            strokeWidth = 12f
        )
    }
}
