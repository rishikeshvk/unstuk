package com.rishikeshvk.unstuk.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.ui.components.StepCard

/**
 * The way past Android's "Restricted setting" block on accessibility services for apps installed from outside
 * an app store: allow it in App info, then turn the service on again.
 */
@Composable
fun RestrictedSettingsHelp(onOpenAppInfo: () -> Unit, modifier: Modifier = Modifier) {
    Column(modifier, verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text(
            stringResource(R.string.access_restricted_title),
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.semantics { heading() }
        )
        Text(
            stringResource(R.string.access_restricted_body),
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        StepCard(1, stringResource(R.string.access_restricted_step_menu))
        StepCard(2, stringResource(R.string.access_restricted_step_again))
        Button(
            onClick = onOpenAppInfo,
            shape = CircleShape,
            modifier = Modifier.heightIn(min = 48.dp)
        ) {
            Text(
                stringResource(R.string.access_restricted_open),
                style = MaterialTheme.typography.labelLarge
            )
        }
    }
}
