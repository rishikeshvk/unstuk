package com.rishikeshvk.unstuk.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.catalog.Area

/** A topic to browse: a tinted icon well and the topic's name. [compact] stacks them for a three-column grid. */
@Composable
fun TopicTile(
    area: Area,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    compact: Boolean = false
) {
    val shape = MaterialTheme.shapes.medium
    val tile = modifier
        .fillMaxWidth()
        .clip(shape)
        .background(MaterialTheme.colorScheme.surface, shape)
        .clickable(role = Role.Button, onClick = onClick)
    if (compact) {
        Column(
            tile
                .heightIn(min = 88.dp)
                .padding(8.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(6.dp, Alignment.CenterVertically)
        ) {
            Icon(
                painterResource(area.icon),
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onTertiaryContainer,
                modifier = Modifier.size(24.dp)
            )
            Text(
                stringResource(area.title),
                style = MaterialTheme.typography.labelMedium,
                textAlign = TextAlign.Center
            )
        }
    } else {
        Row(
            tile
                .heightIn(min = 76.dp)
                .padding(horizontal = 14.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            IconWell(area, size = 40.dp)
            Text(stringResource(area.title), style = MaterialTheme.typography.titleMedium)
        }
    }
}

/** The topic's icon on its tinted, softly squared well. */
@Composable
fun IconWell(area: Area, size: Dp, modifier: Modifier = Modifier) {
    Box(
        modifier
            .size(size)
            .background(MaterialTheme.colorScheme.tertiaryContainer, MaterialTheme.shapes.small),
        contentAlignment = Alignment.Center
    ) {
        Icon(
            painterResource(area.icon),
            contentDescription = null,
            tint = MaterialTheme.colorScheme.onTertiaryContainer,
            modifier = Modifier.size(size * 0.55f)
        )
    }
}
