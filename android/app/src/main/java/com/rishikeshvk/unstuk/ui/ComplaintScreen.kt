package com.rishikeshvk.unstuk.ui

import android.content.Intent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.catalog.FixEntry
import com.rishikeshvk.unstuk.fix.FixSpecs
import com.rishikeshvk.unstuk.flow.ComplaintFlow
import com.rishikeshvk.unstuk.flow.Reply
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** The user types a complaint and gets one reply card; buttons on the card continue the conversation. */
@Composable
fun ComplaintScreen(flow: ComplaintFlow, modifier: Modifier = Modifier) {
    var complaint by remember { mutableStateOf("") }
    var reply by remember { mutableStateOf<Reply?>(null) }
    var busy by remember { mutableStateOf(false) }
    var trialId by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()

    fun respond(next: suspend () -> Reply) {
        busy = true
        scope.launch {
            var result = withContext(Dispatchers.Default) { next() }
            if (result is Reply.Run) {
                reply = result
                val run = result
                result = withContext(Dispatchers.Default) {
                    flow.run(run.intent.id, run.fix.id, run.confidence, trialId)
                }
            }
            reply = result
            busy = false
        }
    }

    val actions = ReplyActions(
        choose = { intentId -> respond { flow.choose(intentId, trialId) } },
        confirm = { r -> respond { flow.run(r.intent.id, r.fix.id, r.confidence, trialId) } },
        decline = { reply = null }
    )

    Column(
        modifier = modifier
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        OutlinedTextField(
            value = complaint,
            onValueChange = { complaint = it },
            label = { Text(stringResource(R.string.complaint_label)) },
            modifier = Modifier.fillMaxWidth(),
            minLines = 2
        )
        Button(
            enabled = !busy && complaint.isNotBlank(),
            onClick = {
                trialId = "ui-${System.currentTimeMillis()}"
                respond { flow.start(complaint, trialId) }
            }
        ) { Text(stringResource(R.string.complaint_submit)) }
        if (busy) Text(stringResource(R.string.working))
        reply?.let { ReplyCard(it, actions, enabled = !busy) }
    }
}

private class ReplyActions(
    val choose: (String) -> Unit,
    val confirm: (Reply.Confirm) -> Unit,
    val decline: () -> Unit
)

@Composable
private fun ReplyCard(reply: Reply, actions: ReplyActions, enabled: Boolean) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            ReplyBody(reply, actions, enabled)
        }
    }
}

@Composable
private fun ReplyBody(reply: Reply, actions: ReplyActions, enabled: Boolean) {
    when (reply) {
        is Reply.Decline -> {
            Title(stringResource(R.string.decline_title))
            Text(stringResource(R.string.decline_body))
            reply.options.forEach { Text("• $it") }
        }
        is Reply.Clarify -> {
            Title(stringResource(R.string.clarify_title))
            reply.intents.forEach { intent ->
                OutlinedButton(
                    enabled = enabled,
                    onClick = { actions.choose(intent.id) },
                    modifier = Modifier.fillMaxWidth()
                ) { Text(intent.option) }
            }
        }
        is Reply.AllClear -> {
            Title(stringResource(R.string.all_clear_title))
            Text(stringResource(R.string.all_clear_body))
            Steps(reply.intent.fallback)
        }
        is Reply.Guide -> GuideCard(reply.fix)
        is Reply.Confirm -> {
            Title(stringResource(R.string.confirm_title, reply.fix.label.lowercaseFirst()))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(enabled = enabled, onClick = { actions.confirm(reply) }) {
                    Text(stringResource(R.string.confirm_yes))
                }
                OutlinedButton(enabled = enabled, onClick = actions.decline) {
                    Text(stringResource(R.string.confirm_no))
                }
            }
        }
        is Reply.Run -> Text(stringResource(R.string.working))
        is Reply.Fixed -> {
            Title(stringResource(R.string.fixed_title, reply.fix.label.lowercaseFirst()))
            reply.next?.let {
                Text(
                    stringResource(R.string.next_title),
                    style = MaterialTheme.typography.labelLarge
                )
                ReplyBody(it, actions, enabled)
            }
        }
        is Reply.AlreadyFine ->
            Title(stringResource(R.string.already_fine_title, reply.fix.label.lowercaseFirst()))
        Reply.NeedsUnlock -> Title(stringResource(R.string.needs_unlock_title))
    }
}

@Composable
private fun GuideCard(fix: FixEntry) {
    val context = LocalContext.current
    Title(stringResource(R.string.guide_title, fix.label.lowercaseFirst()))
    Steps(fix.guide)
    FixSpecs.get(fix.id).settingsAction?.let { action ->
        OutlinedButton(onClick = {
            context.startActivity(Intent(action))
        }) { Text(stringResource(R.string.open_settings)) }
    }
}

@Composable
private fun Title(text: String) {
    Text(text, style = MaterialTheme.typography.titleMedium)
}

@Composable
private fun Steps(steps: List<String>) {
    steps.forEachIndexed { index, step -> Text("${index + 1}. $step") }
}

private fun String.lowercaseFirst() = replaceFirstChar { it.lowercase() }
