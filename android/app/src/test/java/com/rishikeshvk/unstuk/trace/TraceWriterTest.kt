package com.rishikeshvk.unstuk.trace

import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class TraceWriterTest {
    @get:Rule val tmp = TemporaryFolder()

    private val precondition = TraceEvent(1, "t1", "airplane_off", "precondition", "needs_change")
    private val findTile =
        TraceEvent(2, "t1", "airplane_off", "find_tile", "found", strategy = "label")

    @Test
    fun `writes one JSON object per line and omits null fields`() {
        val writer = TraceWriter(tmp.root)

        writer.append(precondition)
        writer.append(findTile)

        assertEquals(
            listOf(
                """{"ts":1,"trialId":"t1","action":"airplane_off","step":"precondition","outcome":"needs_change"}""",
                """{"ts":2,"trialId":"t1","action":"airplane_off","step":"find_tile","outcome":"found","strategy":"label"}"""
            ),
            File(tmp.root, "t1.jsonl").readLines()
        )
    }

    @Test
    fun `reads back the events of one trial in order`() {
        val writer = TraceWriter(tmp.root)
        writer.append(precondition)
        writer.append(findTile)
        writer.append(precondition.copy(trialId = "t2"))

        assertEquals(listOf(precondition, findTile), writer.read("t1"))
    }

    @Test
    fun `reading an unknown trial returns no events`() {
        assertEquals(emptyList<TraceEvent>(), TraceWriter(tmp.root).read("missing"))
    }

    @Test(expected = IllegalArgumentException::class)
    fun `rejects trial ids that could escape the trace directory`() {
        TraceWriter(tmp.root).append(precondition.copy(trialId = "../t1"))
    }
}
