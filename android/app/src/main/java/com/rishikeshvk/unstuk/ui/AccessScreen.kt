package com.rishikeshvk.unstuk.ui

import android.content.Intent
import android.provider.Settings
import androidx.annotation.DrawableRes
import androidx.annotation.StringRes
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.core.net.toUri
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.ui.components.BackTopBar
import com.rishikeshvk.unstuk.ui.components.HintRow
import com.rishikeshvk.unstuk.ui.components.ScreenScaffold
import com.rishikeshvk.unstuk.ui.components.TextLinkButton

/** The special accesses the rungs use, each with a plain reason and a way to Settings to grant it. */
@Composable
fun AccessScreen(status: AccessStatus, onBack: () -> Unit, onDebug: (() -> Unit)?) {
    val context = LocalContext.current
    fun open(intent: Intent) = context.startActivity(intent)
    ScreenScaffold(
        topBar = { BackTopBar(onBack) },
        actions = {
            HintRow(
                R.drawable.ic_offline,
                stringResource(R.string.access_offline),
                iconTint = MaterialTheme.colorScheme.onSurfaceVariant
            )
            onDebug?.let { TextLinkButton(stringResource(R.string.access_debug), onClick = it) }
        }
    ) {
        Text(
            stringResource(R.string.access_title),
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier
                .padding(top = 12.dp)
                .semantics { heading() }
        )
        Text(
            stringResource(R.string.access_body),
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        GrantRow(
            R.drawable.ic_hand,
            R.string.access_service_title,
            R.string.access_service_body,
            status.service
        ) { open(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)) }
        GrantRow(
            R.drawable.ic_moon,
            R.string.access_policy_title,
            R.string.access_policy_body,
            status.policy
        ) { open(Intent(Settings.ACTION_NOTIFICATION_POLICY_ACCESS_SETTINGS)) }
        GrantRow(
            R.drawable.ic_area_screen,
            R.string.access_write_title,
            R.string.access_write_body,
            status.writeSettings
        ) {
            open(
                Intent(
                    Settings.ACTION_MANAGE_WRITE_SETTINGS,
                    "package:${context.packageName}".toUri()
                )
            )
        }
    }
}

@Composable
private fun GrantRow(
    @DrawableRes icon: Int,
    @StringRes title: Int,
    @StringRes body: Int,
    granted: Boolean,
    onAllow: () -> Unit
) {
    val colors = MaterialTheme.colorScheme
    Row(
        Modifier
            .fillMaxWidth()
            .background(colors.surface, MaterialTheme.shapes.large)
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        Box(
            Modifier
                .size(44.dp)
                .background(colors.tertiaryContainer, MaterialTheme.shapes.small),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                painterResource(icon),
                contentDescription = null,
                tint = colors.onTertiaryContainer,
                modifier = Modifier.size(22.dp)
            )
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(stringResource(title), style = MaterialTheme.typography.titleMedium)
            Text(
                stringResource(body),
                style = MaterialTheme.typography.bodySmall,
                color = colors.onSurfaceVariant
            )
        }
        if (granted) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Icon(
                    painterResource(R.drawable.ic_check),
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
                Text(
                    stringResource(R.string.access_on),
                    style = MaterialTheme.typography.labelLarge
                )
            }
        } else {
            Button(
                onClick = onAllow,
                shape = CircleShape,
                modifier = Modifier.heightIn(min = 48.dp)
            ) {
                Text(
                    stringResource(R.string.access_allow),
                    style = MaterialTheme.typography.labelLarge
                )
            }
        }
    }
}
