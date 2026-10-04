package com.rishikeshvk.unstuk.trace

import java.io.File
import kotlinx.serialization.json.Json

private val TRIAL_ID = Regex("[A-Za-z0-9_-]+")

/** Appends trace events as JSON lines, one file per trial, in app-private storage. */
class TraceWriter(private val dir: File) {
    private val json = Json { explicitNulls = false }

    fun append(event: TraceEvent) {
        val file = fileFor(event.trialId)
        file.parentFile?.mkdirs()
        file.appendText(json.encodeToString(event) + "\n")
    }

    fun read(trialId: String): List<TraceEvent> {
        val file = fileFor(trialId)
        if (!file.exists()) return emptyList()
        return file.readLines().map { json.decodeFromString<TraceEvent>(it) }
    }

    // Trial ids arrive from adb in debug builds; reject anything that could escape the trace directory.
    private fun fileFor(trialId: String): File {
        require(TRIAL_ID.matches(trialId)) { "Invalid trial id: $trialId" }
        return File(dir, "$trialId.jsonl")
    }
}
