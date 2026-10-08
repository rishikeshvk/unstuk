package com.rishikeshvk.unstuk.decide

import android.os.Debug
import android.util.Log
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
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

// Spec section 9: the phone must give Python's answers to this.
private const val MAX_DIFFERENCE = 1e-3

/**
 * The app's decision path on every dev line, against Python's int8 answers from `uv run unstuk-device-fixture`,
 * and the timings the M7 results report. Run on the oldest test phone.
 */
@RunWith(AndroidJUnit4::class)
class DecisionModelDeviceTest {
    @Test
    fun decidesAsPythonOnEveryDevLine() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val cases = instrumentation.context.assets.open("dev-decisions.jsonl").bufferedReader()
            .useLines { lines -> lines.map { Json.decodeFromString<DevDecision>(it) }.toList() }
        val nativeBefore = Debug.getNativeHeapAllocatedSize()

        val loadStarted = System.nanoTime()
        DecisionModel.load(instrumentation.targetContext.assets).use { model ->
            val loadMs = (System.nanoTime() - loadStarted) / 1e6
            val nativeMb = (Debug.getNativeHeapAllocatedSize() - nativeBefore) / 1e6
            val timesMs = mutableListOf<Double>()
            var worst = 0.0
            val wrongTop = cases.filter { case ->
                val started = System.nanoTime()
                val choice = model.decide(case.complaint, case.state)
                timesMs += (System.nanoTime() - started) / 1e6
                worst = maxOf(worst, abs(choice.outOfScope - case.outOfScope))
                for ((intent, p) in case.probabilities) {
                    worst = maxOf(worst, abs(choice.probabilities.getValue(intent) - p))
                }
                answer(choice) != expectedAnswer(case)
            }
            val sorted = timesMs.sorted()
            Log.i(
                TAG,
                "load %.0f ms, native heap +%.1f MB; decide p50 %.1f ms, p95 %.1f ms, max %.1f ms over %d lines; "
                    .format(
                        loadMs,
                        nativeMb,
                        sorted.percentile(50),
                        sorted.percentile(95),
                        sorted.last(),
                        cases.size
                    ) +
                    "largest difference %.2e; %d top answers differ".format(worst, wrongTop.size)
            )
            assertEquals("top answers differ on ${wrongTop.map { it.id }}", 0, wrongTop.size)
            assertTrue("largest probability difference $worst", worst <= MAX_DIFFERENCE)
        }
    }

    private fun answer(choice: IntentChoice) =
        choice.top?.key?.takeUnless { choice.declines } ?: "out_of_scope"

    private fun expectedAnswer(case: DevDecision): String {
        val top = case.probabilities.maxBy { it.value }
        return if (case.outOfScope > top.value) "out_of_scope" else top.key
    }

    private fun List<Double>.percentile(p: Int) = this[((size - 1) * p) / 100]
}
