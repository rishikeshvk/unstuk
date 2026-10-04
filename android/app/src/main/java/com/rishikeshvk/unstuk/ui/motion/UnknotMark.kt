package com.rishikeshvk.unstuk.ui.motion

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathMeasure
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.graphics.drawscope.scale
import androidx.compose.ui.res.stringResource
import com.rishikeshvk.unstuk.R

/** The four moments of the logo line (design storyboard "The Unknot"). */
enum class UnknotMotion {
    /** The logo as drawn. */
    STILL,

    /** A bright segment travels the line for as long as a fix runs. */
    LOOP,

    /** The loop pulls straight into a tick; played only after a fresh read confirmed a fix. */
    UNTANGLE,

    /** The knot stays tied and rocks gently: the user's help is needed. */
    WOBBLE,

    /** The plain tick, for "already fine". */
    TICK
}

private const val LOOP_MS = 2200
private const val SEGMENT = 0.35f
private const val GHOST_ALPHA = 0.18f
private const val WOBBLE_DEGREES = 6f
private const val WOBBLE_MS = 700

/** Draws the Unknot in [color]; [strokeWidth] is in the logo's 200 box, so it scales with the mark. */
@Composable
fun UnknotMark(
    motion: UnknotMotion,
    color: Color,
    modifier: Modifier = Modifier,
    strokeWidth: Float = 14f
) {
    val pathData = stringResource(R.string.unknot_path)
    val unknot = remember(pathData) { UnknotPath(pathData) }
    val reduced = rememberReducedMotion()
    val stroke = Stroke(width = strokeWidth, cap = StrokeCap.Round, join = StrokeJoin.Round)
    when {
        reduced || motion == UnknotMotion.STILL -> StaticMark(
            unknot.path(0f),
            color,
            stroke,
            modifier
        )
        motion == UnknotMotion.TICK -> StaticMark(unknot.path(1f), color, stroke, modifier)
        motion == UnknotMotion.LOOP -> LoopingMark(unknot.path(0f), color, stroke, modifier)
        motion == UnknotMotion.UNTANGLE -> UntanglingMark(unknot, color, stroke, modifier)
        else -> WobblingMark(unknot.path(0f), color, stroke, modifier)
    }
}

@Composable
private fun StaticMark(path: Path, color: Color, stroke: Stroke, modifier: Modifier) {
    Canvas(modifier) { inBox { drawPath(path, color, style = stroke) } }
}

@Composable
private fun LoopingMark(path: Path, color: Color, stroke: Stroke, modifier: Modifier) {
    val measure = remember(path) { PathMeasure().apply { setPath(path, false) } }
    val phase by rememberInfiniteTransition(label = "loop").animateFloat(
        initialValue = -SEGMENT,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(LOOP_MS, easing = LinearEasing)),
        label = "phase"
    )
    Canvas(modifier) {
        inBox {
            drawPath(path, color.copy(alpha = GHOST_ALPHA), style = stroke)
            val segment = Path()
            val length = measure.length
            measure.getSegment(
                phase.coerceAtLeast(0f) * length,
                (phase + SEGMENT).coerceAtMost(1f) * length,
                segment,
                true
            )
            drawPath(segment, color, style = stroke)
        }
    }
}

@Composable
private fun UntanglingMark(unknot: UnknotPath, color: Color, stroke: Stroke, modifier: Modifier) {
    val untangle = remember { Animatable(0f) }
    LaunchedEffect(Unit) {
        untangle.animateTo(1f, spring(dampingRatio = Spring.DampingRatioNoBouncy, stiffness = 120f))
    }
    Canvas(modifier) { inBox { drawPath(unknot.path(untangle.value), color, style = stroke) } }
}

@Composable
private fun WobblingMark(path: Path, color: Color, stroke: Stroke, modifier: Modifier) {
    val angle by rememberInfiniteTransition(label = "wobble").animateFloat(
        initialValue = -WOBBLE_DEGREES,
        targetValue = WOBBLE_DEGREES,
        animationSpec = infiniteRepeatable(tween(WOBBLE_MS), RepeatMode.Reverse),
        label = "angle"
    )
    Canvas(modifier) { rotate(angle) { inBox { drawPath(path, color, style = stroke) } } }
}

private inline fun DrawScope.inBox(block: DrawScope.() -> Unit) {
    val factor = minOf(size.width, size.height) / UNKNOT_BOX
    scale(factor, pivot = Offset.Zero, block = block)
}
