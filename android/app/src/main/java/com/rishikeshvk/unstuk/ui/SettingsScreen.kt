package com.rishikeshvk.unstuk.ui

import androidx.annotation.DrawableRes
import androidx.annotation.StringRes
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.BuildConfig
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.ui.components.BackTopBar
import com.rishikeshvk.unstuk.ui.components.ScreenScaffold
import com.rishikeshvk.unstuk.ui.components.dashedBorder
import com.rishikeshvk.unstuk.ui.motion.UnknotMark
import com.rishikeshvk.unstuk.ui.motion.UnknotMotion
import com.rishikeshvk.unstuk.ui.theme.ThemeChoice

private const val ACCESS_GRANTS = 3

/**
 * The app's own settings, one section per concern so later settings slot in as new sections. [onDebug] is null
 * in release builds, which hides the developer section entirely.
 */
@Composable
fun SettingsScreen(
    theme: ThemeChoice,
    onTheme: (ThemeChoice) -> Unit,
    access: AccessStatus,
    onAccess: () -> Unit,
    onBack: () -> Unit,
    onDebug: (() -> Unit)?
) {
    ScreenScaffold(topBar = { BackTopBar(onBack) }) {
        Text(
            stringResource(R.string.settings_title),
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier
                .padding(top = 12.dp)
                .semantics { heading() }
        )
        SectionLabel(R.string.settings_appearance)
        ThemePicker(theme, onTheme)
        SectionLabel(R.string.settings_capabilities)
        val granted = listOf(access.service, access.policy, access.writeSettings).count { it }
        LinkRow(
            R.drawable.ic_shield,
            stringResource(R.string.settings_access),
            stringResource(R.string.settings_access_summary, granted, ACCESS_GRANTS),
            onAccess
        )
        SectionLabel(R.string.settings_about)
        About()
        onDebug?.let {
            SectionLabel(R.string.settings_developers)
            DebugRow(it)
        }
    }
}

@Composable
private fun SectionLabel(@StringRes text: Int) {
    Text(
        stringResource(text),
        style = MaterialTheme.typography.labelLarge,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        modifier = Modifier
            .padding(top = 12.dp)
            .semantics { heading() }
    )
}

private val themeOptions = listOf(
    Triple(ThemeChoice.SYSTEM, R.string.theme_system, R.drawable.ic_system),
    Triple(ThemeChoice.LIGHT, R.string.theme_light, R.drawable.ic_area_screen),
    Triple(ThemeChoice.DARK, R.string.theme_dark, R.drawable.ic_moon)
)

@Composable
private fun ThemePicker(theme: ThemeChoice, onTheme: (ThemeChoice) -> Unit) {
    val colors = MaterialTheme.colorScheme
    val option = RoundedCornerShape(18.dp)
    Row(
        Modifier
            .fillMaxWidth()
            .background(colors.surface, MaterialTheme.shapes.large)
            .padding(6.dp)
            .selectableGroup(),
        horizontalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        themeOptions.forEach { (choice, label, icon) ->
            val selected = choice == theme
            Column(
                Modifier
                    .weight(1f)
                    .heightIn(min = 72.dp)
                    .clip(option)
                    .background(if (selected) colors.primary else colors.surface, option)
                    .selectable(selected = selected, role = Role.RadioButton, onClick = {
                        onTheme(choice)
                    }),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(6.dp, Alignment.CenterVertically)
            ) {
                val tint = if (selected) colors.onPrimary else colors.onSurface
                Icon(
                    painterResource(icon),
                    contentDescription = null,
                    tint = tint,
                    modifier = Modifier.size(22.dp)
                )
                Text(
                    stringResource(label),
                    style = MaterialTheme.typography.titleMedium,
                    color = tint
                )
            }
        }
    }
}

@Composable
private fun LinkRow(@DrawableRes icon: Int, title: String, summary: String, onClick: () -> Unit) {
    val colors = MaterialTheme.colorScheme
    val shape = MaterialTheme.shapes.large
    Row(
        Modifier
            .fillMaxWidth()
            .clip(shape)
            .background(colors.surface, shape)
            .clickable(role = Role.Button, onClick = onClick)
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
            Text(title, style = MaterialTheme.typography.titleMedium)
            Text(
                summary,
                style = MaterialTheme.typography.bodySmall,
                color = colors.onSurfaceVariant
            )
        }
        Icon(
            painterResource(R.drawable.ic_chevron_right),
            contentDescription = null,
            modifier = Modifier.size(20.dp)
        )
    }
}

@Composable
private fun About() {
    val colors = MaterialTheme.colorScheme
    Column(
        Modifier
            .fillMaxWidth()
            .background(colors.surface, MaterialTheme.shapes.large)
            .padding(horizontal = 16.dp, vertical = 4.dp)
    ) {
        Row(
            Modifier.heightIn(min = 56.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            UnknotMark(UnknotMotion.STILL, colors.tertiary, Modifier.size(24.dp), strokeWidth = 18f)
            Text(
                stringResource(R.string.app_name),
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.weight(1f)
            )
            Text(
                stringResource(R.string.settings_version, BuildConfig.VERSION_NAME),
                style = MaterialTheme.typography.bodySmall,
                color = colors.onSurfaceVariant
            )
        }
        HorizontalDivider(color = colors.outlineVariant)
        Row(
            Modifier.heightIn(min = 56.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Icon(
                painterResource(R.drawable.ic_offline),
                contentDescription = null,
                tint = colors.onSurfaceVariant,
                modifier = Modifier.size(24.dp)
            )
            Text(
                stringResource(R.string.access_offline),
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}

/** Dashed, unlike every user-facing row: a visible reminder that this one is for developers. */
@Composable
private fun DebugRow(onClick: () -> Unit) {
    val colors = MaterialTheme.colorScheme
    val shape = MaterialTheme.shapes.large
    Row(
        Modifier
            .fillMaxWidth()
            .clip(shape)
            .dashedBorder(colors.outline)
            .clickable(role = Role.Button, onClick = onClick)
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        Icon(
            painterResource(R.drawable.ic_terminal),
            contentDescription = null,
            modifier = Modifier.size(24.dp)
        )
        Text(
            stringResource(R.string.settings_debug),
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.weight(1f)
        )
        Text(
            stringResource(R.string.settings_debug_badge),
            style = MaterialTheme.typography.labelMedium,
            color = colors.onTertiaryContainer,
            modifier = Modifier
                .background(colors.tertiaryContainer, MaterialTheme.shapes.small)
                .padding(horizontal = 8.dp, vertical = 2.dp)
        )
    }
}
