package com.rishikeshvk.unstuk.ui.reply

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.flow.Reply
import com.rishikeshvk.unstuk.ui.components.BackTopBar
import com.rishikeshvk.unstuk.ui.components.OptionCard
import com.rishikeshvk.unstuk.ui.components.ScreenScaffold
import com.rishikeshvk.unstuk.ui.components.TextLinkButton

// A speech bubble: the user's own words, quoted back.
private val Bubble = RoundedCornerShape(20.dp, 20.dp, 20.dp, 6.dp)

/** More than one issue fits: the user's words, then at most three plain options and a way out. */
@Composable
fun ClarifyReply(reply: Reply.Clarify, complaint: String, actions: ReplyActions) {
    ScreenScaffold(topBar = { BackTopBar(actions.back) }) {
        if (complaint.isNotBlank()) {
            Text(
                stringResource(R.string.clarify_said, complaint.trim()),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier
                    .padding(top = 12.dp)
                    .background(MaterialTheme.colorScheme.surface, Bubble)
                    .padding(horizontal = 16.dp, vertical = 10.dp)
            )
        }
        Text(
            stringResource(R.string.clarify_title),
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier
                .padding(top = 8.dp, bottom = 8.dp)
                .semantics { heading() }
        )
        reply.intents.forEach { intent ->
            OptionCard(intent.option, onClick = { actions.pick(intent.id) })
        }
        TextLinkButton(
            stringResource(R.string.clarify_none),
            onClick = actions.noneOfThese,
            modifier = Modifier.align(Alignment.CenterHorizontally)
        )
    }
}
