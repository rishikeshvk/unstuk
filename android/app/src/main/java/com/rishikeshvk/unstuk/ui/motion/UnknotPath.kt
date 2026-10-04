package com.rishikeshvk.unstuk.ui.motion

import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.lerp
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.vector.PathNode
import androidx.compose.ui.graphics.vector.PathParser

/** The tick's short arm in the logo's 200 box: where the straightened line starts, back from the tick's corner. */
private val SHORT_ARM = Offset(28f, 24f)

/** The logo's 200 box, the space [UnknotPath] draws in. */
const val UNKNOT_BOX = 200f

/**
 * The Unknot, parsed from the same path string as the launcher icon. [path] blends between the knot (0) and a
 * plain tick (1) by sliding every point before the tick's corner onto its short arm, so the line pulls straight.
 */
class UnknotPath(pathData: String) {
    private val nodes = PathParser().parsePathString(pathData).toNodes()
    private val knot: List<Offset> = nodes.flatMap(::pointsOf)
    private val straight: List<Offset> = straighten(knot)

    fun path(untangle: Float): Path {
        val points = knot.zip(straight) { k, s -> lerp(k, s, untangle) }.iterator()
        return Path().apply {
            for (node in nodes) {
                when (node) {
                    is PathNode.MoveTo -> points.next().let { moveTo(it.x, it.y) }
                    is PathNode.LineTo -> points.next().let { lineTo(it.x, it.y) }
                    is PathNode.CurveTo -> {
                        val (a, b, c) = Triple(points.next(), points.next(), points.next())
                        cubicTo(a.x, a.y, b.x, b.y, c.x, c.y)
                    }
                    else -> error("The Unknot uses absolute M, C and L commands only, not $node")
                }
            }
        }
    }

    private fun pointsOf(node: PathNode): List<Offset> = when (node) {
        is PathNode.MoveTo -> listOf(Offset(node.x, node.y))
        is PathNode.LineTo -> listOf(Offset(node.x, node.y))
        is PathNode.CurveTo -> listOf(
            Offset(node.x1, node.y1),
            Offset(node.x2, node.y2),
            Offset(node.x3, node.y3)
        )
        else -> error("The Unknot uses absolute M, C and L commands only, not $node")
    }

    // The last point is the tick's tip and the one before it its corner; everything earlier collapses evenly
    // onto the short arm that ends at the corner. The tick then moves to the knot's centre, so the mark stays put.
    private fun straighten(points: List<Offset>): List<Offset> {
        val corner = points[points.size - 2]
        val start = corner - SHORT_ARM
        val lead = points.size - 1
        val tick = points.mapIndexed { i, point ->
            if (i >= lead) point else lerp(start, corner, i / (lead - 1f))
        }
        val shift = centre(points) - centre(tick)
        return tick.map { it + shift }
    }

    private fun centre(points: List<Offset>) = Offset(
        (points.minOf { it.x } + points.maxOf { it.x }) / 2,
        (points.minOf { it.y } + points.maxOf { it.y }) / 2
    )
}
