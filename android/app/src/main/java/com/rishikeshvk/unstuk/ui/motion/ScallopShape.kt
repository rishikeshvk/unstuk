package com.rishikeshvk.unstuk.ui.motion

import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Outline
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.LayoutDirection
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

private const val STEPS = 144

/**
 * A circle whose radius dips [depth] (a fraction of it) between [lobes] bumps: the "cookie" behind progress and
 * success, and with more, deeper lobes the "burst" for moments that need the user. Depth 0 is a plain circle.
 */
class ScallopShape(private val lobes: Int, private val depth: Float) : Shape {
    override fun createOutline(
        size: Size,
        layoutDirection: LayoutDirection,
        density: Density
    ): Outline {
        val radius = minOf(size.width, size.height) / 2
        val path = Path()
        for (i in 0 until STEPS) {
            val angle = 2 * PI * i / STEPS
            val r = radius * (1 - depth * (1 - cos(lobes * angle)) / 2)
            val x = size.width / 2 + (r * sin(angle)).toFloat()
            val y = size.height / 2 - (r * cos(angle)).toFloat()
            if (i == 0) path.moveTo(x, y) else path.lineTo(x, y)
        }
        path.close()
        return Outline.Generic(path)
    }

    companion object {
        val Cookie = ScallopShape(lobes = 9, depth = 0.16f)
        val Burst = ScallopShape(lobes = 8, depth = 0.22f)
    }
}
