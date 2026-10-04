package com.rishikeshvk.unstuk.ui

import android.content.Intent
import android.provider.Settings
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.core.net.toUri
import androidx.lifecycle.compose.LifecycleResumeEffect
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.a11y.UnstukService
import com.rishikeshvk.unstuk.fix.Grant

/** The special accesses the rungs need, each with a button to the Settings screen that grants it. */
@Composable
fun SetupScreen(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val service by UnstukService.connected.collectAsStateWithLifecycle()
    // Grants change in Settings, outside the app; re-read them whenever the screen comes back.
    var refresh by remember { mutableIntStateOf(0) }
    LifecycleResumeEffect(Unit) {
        refresh++
        onPauseOrDispose {}
    }
    Column(
        modifier = modifier.padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(stringResource(R.string.setup_title), style = MaterialTheme.typography.titleLarge)
        Text(stringResource(R.string.setup_body))
        GrantRow(stringResource(R.string.setup_service), service != null) {
            context.startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }
        key(refresh) {
            GrantRow(
                stringResource(R.string.setup_policy),
                Grant.NOTIFICATION_POLICY.isGranted(context)
            ) {
                context.startActivity(Intent(Settings.ACTION_NOTIFICATION_POLICY_ACCESS_SETTINGS))
            }
            GrantRow(
                stringResource(R.string.setup_write_settings),
                Grant.WRITE_SETTINGS.isGranted(context)
            ) {
                context.startActivity(
                    Intent(
                        Settings.ACTION_MANAGE_WRITE_SETTINGS,
                        "package:${context.packageName}".toUri()
                    )
                )
            }
        }
    }
}

@Composable
private fun GrantRow(label: String, granted: Boolean, open: () -> Unit) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(label, modifier = Modifier.weight(1f))
        if (granted) {
            Text(
                stringResource(R.string.setup_granted),
                style = MaterialTheme.typography.labelLarge
            )
        } else {
            Button(onClick = open) { Text(stringResource(R.string.setup_grant)) }
        }
    }
}
