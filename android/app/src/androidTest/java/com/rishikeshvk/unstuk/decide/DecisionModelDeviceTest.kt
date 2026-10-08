package com.rishikeshvk.unstuk.decide

import android.os.Debug
import android.util.Log
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.rishikeshvk.unstuk.catalog.CatalogLoader
import com.rishikeshvk.unstuk.catalog.GateLines
import kotlin.math.abs
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@Serializable
private data class DevDecision(
    val id: String,
    val complaint: String,
    val state: String,
    val probabilities: Map<String, Double>,
    @SerialName("out_of_scope") val outOfScope: Double
)

private const val TAG = "UnstukBench"

// Spec correction: the same top answer on every line, the same gate outcome on nearly all of them.
private const val MIN_OUTCOME_AGREEMENT = 0.99

/**
 * The app's decision path on every dev line, against Python's answers from `uv run unstuk-device-fixture`, and
 * the timings the M7 results report. Run on the oldest test phone.
 */
@RunWith(AndroidJUnit4::class)
class DecisionModelDeviceTest {
    @Test
    fun decidesAsPythonOnEveryDevLine() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val assets = instrumentation.targetContext.assets
        val gate = CatalogLoader.loadGate(assets)
        val cases = instrumentation.context.assets.open("dev-decisions.jsonl").bufferedReader()
            .useLines { lines -> lines.map { Json.decodeFromString<DevDecision>(it) }.toList() }
        val nativeBefore = Debug.getNativeHeapAllocatedSize()

        val loadStarted = System.nanoTime()
        DecisionModel.load(assets).use { model ->
            val loadMs = (System.nanoTime() - loadStarted) / 1e6
            val nativeMb = (Debug.getNativeHeapAllocatedSize() - nativeBefore) / 1e6
            val timesMs = mutableListOf<Double>()
            val gaps = mutableListOf<Double>()
            val wrongTop = mutableListOf<String>()
            var sameOutcome = 0
            for (case in cases) {
                val started = System.nanoTime()
                val choice = model.decide(case.complaint, case.state)
                timesMs += (System.nanoTime() - started) / 1e6
                val expected = IntentChoice(case.probabilities, case.outOfScope)
                gaps +=
                    expected.probabilities.maxOf { (intent, p) ->
                        abs(
                            choice.probabilities.getValue(intent) - p
                        )
                    }
                        .coerceAtLeast(abs(choice.outOfScope - case.outOfScope))
                if (answer(choice) != answer(expected)) wrongTop += case.id
                if (outcome(choice, gate) == outcome(expected, gate)) sameOutcome++
            }
            val agreement = sameOutcome.toDouble() / cases.size
            val times = timesMs.sorted()
            val sortedGaps = gaps.sorted()
            Log.i(
                TAG,
                "load %.0f ms, native heap +%.1f MB; decide p50 %.1f ms, p95 %.1f ms, max %.1f ms over %d lines; "
                    .format(
                        loadMs,
                        nativeMb,
                        times.percentile(50),
                        times.percentile(95),
                        times.last(),
                        cases.size
                    ) +
                    "gap p50 %.1e, p95 %.1e, max %.1e; %d top answers differ; gate outcomes agree %.2f%%"
                        .format(
                            sortedGaps.percentile(50),
                            sortedGaps.percentile(95),
                            sortedGaps.last(),
                            wrongTop.size,
                            100 * agreement
                        )
            )
            assertEquals("top answers differ on $wrongTop", 0, wrongTop.size)
            assertTrue("gate outcomes agree on $agreement", agreement >= MIN_OUTCOME_AGREEMENT)
        }
    }

    private fun answer(choice: IntentChoice) =
        choice.top?.key?.takeUnless { choice.declines } ?: "out_of_scope"

    /** What the gate does before diagnosis, as `evaluate.Scored.outcome` defines it. */
    private fun outcome(choice: IntentChoice, gate: GateLines): String {
        val top = choice.top
        return when {
            top == null || choice.declines -> "decline"
            RiskGate(gate).isTooUncertain(choice) -> "clarify"
            top.value >= gate.automaticAt -> "automatic"
            else -> "confirm"
        }
    }

    private fun List<Double>.percentile(p: Int) = this[((size - 1) * p) / 100]
}
