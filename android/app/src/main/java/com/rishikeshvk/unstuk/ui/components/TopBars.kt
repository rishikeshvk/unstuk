package com.rishikeshvk.unstuk.ui.components

import androidx.annotation.DrawableRes
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.ui.motion.UnknotMark
import com.rishikeshvk.unstuk.ui.motion.UnknotMotion

/** Home's bar: the mark and wordmark, and the Access button with a dot while something is not granted. */
@Composable
fun HomeTopBar(onAccess: () -> Unit, accessMissing: Boolean) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(64.dp)
            .padding(start = 20.dp, end = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        UnknotMark(
            UnknotMotion.STILL,
            MaterialTheme.colorScheme.tertiary,
            Modifier.size(32.dp),
            strokeWidth = 17f
        )
        Text(
            stringResource(R.string.app_name).lowercase(),
            style = MaterialTheme.typography.headlineSmall,
            modifier = Modifier
                .padding(start = 8.dp)
                .weight(1f)
        )
        Box {
            RoundIconButton(R.drawable.ic_shield, stringResource(R.string.open_access), onAccess)
            if (accessMissing) {
                Box(
                    Modifier
                        .align(Alignment.TopEnd)
                        .offset(x = (-8).dp, y = 8.dp)
                        .size(12.dp)
                        .background(MaterialTheme.colorScheme.tertiary, CircleShape)
                        .border(2.dp, MaterialTheme.colorScheme.surface, CircleShape)
                )
            }
        }
    }
}

/** Every other screen's bar: a back button, nothing else to choose. */
@Composable
fun BackTopBar(onBack: () -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(64.dp)
            .padding(horizontal = 12.dp),
        horizontalArrangement = Arrangement.Start,
        verticalAlignment = Alignment.CenterVertically
    ) {
        RoundIconButton(R.drawable.ic_back, stringResource(R.string.back), onBack)
    }
}

@Composable
private fun RoundIconButton(@DrawableRes icon: Int, description: String, onClick: () -> Unit) {
    IconButton(
        onClick = onClick,
        modifier = Modifier.size(48.dp),
        colors = IconButtonDefaults.iconButtonColors(
            containerColor = MaterialTheme.colorScheme.surface,
            contentColor = MaterialTheme.colorScheme.onSurface
        )
    ) {
        Icon(
            painterResource(icon),
            contentDescription = description,
            modifier = Modifier.size(22.dp)
        )
    }
}
