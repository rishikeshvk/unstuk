package com.rishikeshvk.unstuk.ui.reply

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.catalog.FixEntry
import com.rishikeshvk.unstuk.ui.components.HeroState
import com.rishikeshvk.unstuk.ui.components.StatusHero

/** A fix is running: the line loops, the screen says what is being worked on and what the user will see. */
@Composable
fun WorkingReply(fix: FixEntry) {
    Column(
        Modifier
            .fillMaxSize()
            .padding(20.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(20.dp, Alignment.CenterVertically)
    ) {
        StatusHero(HeroState.WORKING, size = 200.dp)
        Text(
            stringResource(R.string.working_title, fix.subject),
            style = MaterialTheme.typography.headlineMedium,
            textAlign = TextAlign.Center,
            modifier = Modifier
                .widthIn(max = 320.dp)
                .semantics { liveRegion = LiveRegionMode.Polite }
        )
        RungHint(fix, Modifier.widthIn(max = 340.dp))
    }
}
