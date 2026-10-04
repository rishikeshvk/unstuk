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
import com.rishikeshvk.unstuk.catalog.IntentEntry
import com.rishikeshvk.unstuk.diagnose.ScanRow
import com.rishikeshvk.unstuk.ui.components.BackTopBar
import com.rishikeshvk.unstuk.ui.components.PrimaryButton
import com.rishikeshvk.unstuk.ui.components.ScreenScaffold
import com.rishikeshvk.unstuk.ui.components.StepCard
import com.rishikeshvk.unstuk.ui.motion.DiagnosisScan

/**
 * The intent's own tips. With a [scan] it answers "everything I can check looks fine" (the all-clear reply);
 * without one it follows "Still not working?" after a fix.
 */
@Composable
fun TipsReply(
    intent: IntentEntry,
    scan: List<ScanRow>?,
    fixed: Set<String>,
    actions: ReplyActions
) {
    ScreenScaffold(
        topBar = { BackTopBar(actions.back) },
        actions = { PrimaryButton(stringResource(R.string.done), onClick = actions.finish) }
    ) {
        if (scan != null) {
            Text(
                stringResource(R.string.all_clear_title),
                style = MaterialTheme.typography.headlineMedium,
                modifier = Modifier
                    .padding(top = 12.dp)
                    .semantics { heading() }
            )
            DiagnosisScan(scan, fixed)
        }
        Text(
            stringResource(R.string.tips_title),
            style = if (scan ==
                null
            ) {
                MaterialTheme.typography.headlineMedium
            } else {
                MaterialTheme.typography.labelLarge
            },
            color = if (scan ==
                null
            ) {
                MaterialTheme.colorScheme.onBackground
            } else {
                MaterialTheme.colorScheme.onSurfaceVariant
            },
            modifier = Modifier
                .padding(top = 12.dp)
                .semantics { heading() }
        )
        intent.fallback.forEachIndexed { index, tip -> StepCard(index + 1, tip, accent = true) }
    }
}
