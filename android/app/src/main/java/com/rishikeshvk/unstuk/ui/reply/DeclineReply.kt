package com.rishikeshvk.unstuk.ui.reply

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.catalog.Area
import com.rishikeshvk.unstuk.ui.components.BackTopBar
import com.rishikeshvk.unstuk.ui.components.ComplaintField
import com.rishikeshvk.unstuk.ui.components.HeroState
import com.rishikeshvk.unstuk.ui.components.PrimaryButton
import com.rishikeshvk.unstuk.ui.components.ScreenScaffold
import com.rishikeshvk.unstuk.ui.components.TopicTile

private const val TOPICS_PER_ROW = 3

/** Nothing matched: keep the user's words to edit, and offer topics instead of the whole list. */
@Composable
fun DeclineReply(complaint: String, actions: ReplyActions) {
    ScreenScaffold(topBar = { BackTopBar(actions.back) }) {
        HeroTitle(HeroState.NEEDS_YOU, stringResource(R.string.decline_title), heroSize = 72.dp)
        Text(
            stringResource(R.string.decline_body),
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        ComplaintField(complaint, actions.updateComplaint, actions.submit, highlight = true)
        PrimaryButton(
            stringResource(R.string.decline_retry),
            onClick = actions.submit,
            enabled = complaint.isNotBlank()
        )
        Text(
            stringResource(R.string.home_topics),
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier
                .padding(top = 12.dp)
                .semantics { heading() }
        )
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Area.entries.chunked(TOPICS_PER_ROW).forEach { row ->
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    row.forEach { area ->
                        TopicTile(
                            area,
                            onClick = { actions.openTopic(area) },
                            modifier = Modifier.weight(1f),
                            compact = true
                        )
                    }
                }
            }
        }
    }
}
