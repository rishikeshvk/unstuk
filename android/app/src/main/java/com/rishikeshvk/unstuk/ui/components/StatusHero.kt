package com.rishikeshvk.unstuk.ui.components

import android.os.Build
import android.view.HapticFeedbackConstants
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.ui.motion.ScallopShape
import com.rishikeshvk.unstuk.ui.motion.UnknotMark
import com.rishikeshvk.unstuk.ui.motion.UnknotMotion
import com.rishikeshvk.unstuk.ui.motion.rememberReducedMotion

private const val SPIN_MS = 9000

enum class HeroState { WORKING, DONE, NEEDS_YOU, CALM }

/**
 * The shape-and-line illustration at the top of a reply. Purely decorative for screen readers: every state is
 * also said in the screen's text. Done gives a confirm haptic, since it appears only after a verified fix.
 */
@Composable
fun StatusHero(state: HeroState, modifier: Modifier = Modifier, size: Dp = 104.dp) {
    val colors = MaterialTheme.colorScheme
    val view = LocalView.current
    if (state == HeroState.DONE) {
        LaunchedEffect(Unit) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                view.performHapticFeedback(HapticFeedbackConstants.CONFIRM)
            }
        }
    }
    Box(modifier.size(size)) {
        val backdrop = Modifier.fillMaxSize()
        when (state) {
            HeroState.WORKING -> SpinningCookie(backdrop)
            HeroState.DONE -> Box(backdrop.background(colors.tertiary, ScallopShape.Cookie))
            HeroState.NEEDS_YOU -> Box(
                backdrop.background(colors.tertiaryContainer, ScallopShape.Burst)
            )
            HeroState.CALM -> Box(
                backdrop
                    .background(colors.surface, ScallopShape.Cookie)
                    .border(3.dp, colors.onSurface, ScallopShape.Cookie)
            )
        }
        val mark = Modifier
            .fillMaxSize()
            .padding(size * 0.15f)
        when (state) {
            HeroState.WORKING -> UnknotMark(
                UnknotMotion.LOOP,
                colors.onSurface,
                mark,
                strokeWidth = 13f
            )
            HeroState.DONE -> UnknotMark(
                UnknotMotion.UNTANGLE,
                colors.onTertiary,
                mark,
                strokeWidth = 16f
            )
            HeroState.NEEDS_YOU ->
                UnknotMark(UnknotMotion.WOBBLE, colors.onTertiaryContainer, mark, strokeWidth = 16f)
            HeroState.CALM -> UnknotMark(
                UnknotMotion.TICK,
                colors.onSurface,
                mark,
                strokeWidth = 14f
            )
        }
    }
}

@Composable
private fun SpinningCookie(modifier: Modifier) {
    val reduced = rememberReducedMotion()
    val angle by rememberInfiniteTransition(label = "cookie").animateFloat(
        initialValue = 0f,
        targetValue = if (reduced) 0f else 360f,
        animationSpec = infiniteRepeatable(tween(SPIN_MS, easing = LinearEasing)),
        label = "angle"
    )
    Box(
        modifier
            .rotate(angle)
            .background(MaterialTheme.colorScheme.tertiaryContainer, ScallopShape.Cookie)
    )
}
