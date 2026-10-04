package com.rishikeshvk.unstuk.ui.reply

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.catalog.FixEntry
import com.rishikeshvk.unstuk.flow.Reply
import com.rishikeshvk.unstuk.ui.components.BackTopBar
import com.rishikeshvk.unstuk.ui.components.Panel
import com.rishikeshvk.unstuk.ui.components.PrimaryButton
import com.rishikeshvk.unstuk.ui.components.ScreenScaffold
import com.rishikeshvk.unstuk.ui.components.TextLinkButton
import com.rishikeshvk.unstuk.ui.motion.DiagnosisScan

/**
 * The gate wants a yes: what was found and why it matters, what was checked, what will happen, and a button
 * named after the action itself rather than "Yes".
 */
@Composable
fun ConfirmReply(reply: Reply.Confirm, fixed: Set<String>, actions: ReplyActions) {
    ScreenScaffold(
        topBar = { BackTopBar(actions.back) },
        actions = {
            PrimaryButton(
                reply.fix.label,
                onClick = { actions.confirm(reply.intent.id, reply.fix, reply.confidence) }
            )
            TextLinkButton(stringResource(R.string.not_now), onClick = actions.back)
        }
    ) {
        Finding(reply.fix, Modifier.padding(top = 8.dp))
        DiagnosisScan(reply.scan, fixed)
        RungHint(reply.fix)
    }
}

/** The badge, the finding as a headline and its reason. Also the body of the "one more thing" card. */
@Composable
fun Finding(fix: FixEntry, modifier: Modifier = Modifier) {
    Panel(modifier) {
        Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
            FoundBadge()
            Text(
                fix.finding,
                style = MaterialTheme.typography.headlineMedium,
                modifier = Modifier.semantics { heading() }
            )
            fix.why?.let {
                Text(
                    it,
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
private fun FoundBadge() {
    val colors = MaterialTheme.colorScheme
    Row(
        Modifier
            .background(colors.tertiaryContainer, MaterialTheme.shapes.small)
            .padding(start = 8.dp, end = 12.dp, top = 6.dp, bottom = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Box(
            Modifier
                .size(20.dp)
                .background(colors.tertiary, CircleShape),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                painterResource(R.drawable.ic_alert),
                contentDescription = null,
                tint = colors.onTertiary,
                modifier = Modifier.size(12.dp)
            )
        }
        Text(
            stringResource(R.string.found_badge),
            style = MaterialTheme.typography.labelLarge,
            color = colors.onTertiaryContainer
        )
    }
}
