package com.rishikeshvk.unstuk.ui.reply

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
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
import com.rishikeshvk.unstuk.flow.FixStep
import com.rishikeshvk.unstuk.flow.Reply
import com.rishikeshvk.unstuk.ui.components.HeroState
import com.rishikeshvk.unstuk.ui.components.Panel
import com.rishikeshvk.unstuk.ui.components.PrimaryButton
import com.rishikeshvk.unstuk.ui.components.ScreenScaffold
import com.rishikeshvk.unstuk.ui.components.SecondaryButton
import com.rishikeshvk.unstuk.ui.components.TextLinkButton
import com.rishikeshvk.unstuk.ui.motion.DiagnosisScan
import com.rishikeshvk.unstuk.ui.motion.HowFixedTimeline

/**
 * A fresh read confirmed the fix: the line pulls straight, the success line says exactly what changed, and if
 * another cause still holds it is offered as one next card, never run on its own.
 */
@Composable
fun FixedReply(
    reply: Reply.Fixed,
    fixed: Set<String>,
    howFixed: List<FixStep>,
    actions: ReplyActions
) {
    val next = reply.next
    ScreenScaffold(
        actions = {
            if (next == null) {
                PrimaryButton(stringResource(R.string.done), onClick = actions.finish)
                TextLinkButton(
                    stringResource(R.string.still_not_working),
                    onClick = { actions.showTips(reply.intent) }
                )
            } else {
                SecondaryButton(stringResource(R.string.done_secondary), onClick = actions.finish)
            }
        }
    ) {
        HeroTitle(
            HeroState.DONE,
            reply.fix.done,
            subtitle = stringResource(R.string.fixed_subtitle)
        )
        if (next == null) DiagnosisScan(reply.scan, fixed, Modifier.padding(top = 12.dp))
        HowFixedTimeline(howFixed)
        next?.let { NextCard(it, actions) }
    }
}

@Composable
private fun NextCard(next: Reply, actions: ReplyActions) {
    val (fix, action) = when (next) {
        is Reply.Confirm ->
            next.fix to
                { actions.confirm(next.intent.id, next.fix, next.confidence) }
        is Reply.Guide -> next.fix to { actions.showReply(next) }
        else -> error("A next cause is offered as a confirm or a guide, not $next")
    }
    val label = if (next is Reply.Confirm) fix.label else stringResource(R.string.show_me_how)
    Panel(Modifier.padding(top = 12.dp)) {
        Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Text(
                stringResource(R.string.next_title),
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Text(
                fix.finding,
                style = MaterialTheme.typography.headlineSmall,
                modifier = Modifier.semantics { heading() }
            )
            fix.why?.let {
                Text(
                    it,
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            PrimaryButton(label, onClick = action)
        }
    }
}
