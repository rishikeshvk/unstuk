package com.rishikeshvk.unstuk.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.catalog.Area
import com.rishikeshvk.unstuk.catalog.IntentEntry
import com.rishikeshvk.unstuk.ui.components.BackTopBar
import com.rishikeshvk.unstuk.ui.components.IconWell
import com.rishikeshvk.unstuk.ui.components.OptionCard
import com.rishikeshvk.unstuk.ui.components.Panel
import com.rishikeshvk.unstuk.ui.components.ScreenScaffold
import com.rishikeshvk.unstuk.ui.components.title

/** The few problems under one topic. The tapped tile grows into this screen (a container transform). */
@Composable
fun TopicScreen(
    area: Area,
    intents: List<IntentEntry>,
    onPick: (String) -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    ScreenScaffold(
        modifier.background(MaterialTheme.colorScheme.background),
        topBar = { BackTopBar(onBack) }
    ) {
        Panel(Modifier.padding(top = 12.dp)) {
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                IconWell(area, size = 64.dp)
                Text(
                    stringResource(area.title),
                    style = MaterialTheme.typography.headlineMedium,
                    modifier = Modifier.semantics { heading() }
                )
                Text(
                    stringResource(R.string.topic_question),
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
        intents.forEach { intent -> OptionCard(intent.option, onClick = { onPick(intent.id) }) }
        Text(
            stringResource(R.string.topic_footer),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 12.dp)
        )
    }
}
