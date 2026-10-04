package com.rishikeshvk.unstuk.ui.reply

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
import com.rishikeshvk.unstuk.flow.Reply
import com.rishikeshvk.unstuk.ui.components.HeroState
import com.rishikeshvk.unstuk.ui.components.PrimaryButton
import com.rishikeshvk.unstuk.ui.components.ScreenScaffold
import com.rishikeshvk.unstuk.ui.components.StatusHero
import com.rishikeshvk.unstuk.ui.components.TextLinkButton

/** The setting was already right when the fix started: say so calmly, and offer the intent's other tips. */
@Composable
fun AlreadyFineReply(reply: Reply.AlreadyFine, actions: ReplyActions) {
    ScreenScaffold(
        actions = {
            PrimaryButton(stringResource(R.string.done), onClick = actions.finish)
            TextLinkButton(
                stringResource(R.string.still_not_working),
                onClick = { actions.showTips(reply.intent) }
            )
        }
    ) {
        StatusHero(HeroState.CALM, Modifier.padding(top = 24.dp))
        Text(
            reply.fix.done,
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier
                .padding(top = 8.dp)
                .semantics { heading() }
        )
        Text(
            stringResource(R.string.already_fine_body),
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}
