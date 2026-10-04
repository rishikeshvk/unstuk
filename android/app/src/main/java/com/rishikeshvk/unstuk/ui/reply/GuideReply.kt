package com.rishikeshvk.unstuk.ui.reply

import android.content.Intent
import android.os.Build
import android.view.HapticFeedbackConstants
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.catalog.Risk
import com.rishikeshvk.unstuk.fix.FixSpecs
import com.rishikeshvk.unstuk.flow.Reply
import com.rishikeshvk.unstuk.ui.components.BackTopBar
import com.rishikeshvk.unstuk.ui.components.HeroState
import com.rishikeshvk.unstuk.ui.components.PrimaryButton
import com.rishikeshvk.unstuk.ui.components.ScreenScaffold
import com.rishikeshvk.unstuk.ui.components.SecondaryButton
import com.rishikeshvk.unstuk.ui.components.StepCard
import com.rishikeshvk.unstuk.ui.components.TextLinkButton

/**
 * Steps for the user to follow, with the reason they are steps: the fix is risky, nothing could do it, or it
 * still looks the same. "Check for me" closes the loop with a fresh read, when the cause is a real check.
 */
@Composable
fun GuideReply(reply: Reply.Guide, actions: ReplyActions) {
    val context = LocalContext.current
    val view = LocalView.current
    val fix = reply.fix
    val risky = fix.risk == Risk.HIGH
    val attemptFailed = reply.reason != null || reply.stillFound
    if (attemptFailed) {
        LaunchedEffect(reply) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                view.performHapticFeedback(HapticFeedbackConstants.REJECT)
            }
        }
    }
    val settings = FixSpecs.get(fix.id).settingsAction
    val checkable = reply.scan.any { it.fix.id == fix.id }
    ScreenScaffold(
        topBar = { BackTopBar(actions.back) },
        actions = {
            settings?.let {
                PrimaryButton(
                    stringResource(R.string.open_settings),
                    onClick = { context.startActivity(Intent(it)) },
                    trailingIcon = R.drawable.ic_open_external
                )
            }
            if (checkable) {
                SecondaryButton(
                    stringResource(R.string.check_for_me),
                    onClick = { actions.recheck(reply) }
                )
            } else {
                TextLinkButton(stringResource(R.string.not_now), onClick = actions.back)
            }
        }
    ) {
        val title = when {
            risky -> fix.label
            reply.stillFound -> stringResource(R.string.guide_still_title)
            else -> stringResource(R.string.guide_together_title)
        }
        HeroTitle(HeroState.NEEDS_YOU, title, heroSize = 72.dp)
        Text(
            when {
                risky -> stringResource(R.string.guide_risky_body)
                reply.stillFound -> fix.finding + " " + stringResource(R.string.guide_still_body)
                else -> stringResource(R.string.guide_together_body)
            },
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        fix.guide.forEachIndexed { index, step -> StepCard(index + 1, step) }
    }
}
