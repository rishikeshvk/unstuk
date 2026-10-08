package com.rishikeshvk.unstuk.decide

import java.io.File
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

@Serializable
private data class Encoding(
    val a: String,
    val b: String?,
    val ids: List<Long>,
    @SerialName("type_ids") val typeIds: List<Long>
)

private const val MAX_TOKENS = 128

/**
 * Python's `tokenizers` on every text in `wordpiece.jsonl`; any drift would feed the model ids it never saw.
 * Both files are generated: `uv run unstuk-export assets` and `uv run unstuk-token-fixture` in ml/.
 */
class WordPieceParityTest {
    private val vocab = File("src/main/assets/model/vocab.txt")
    private val fixture = File("src/test/resources/wordpiece.jsonl")
    private val wordPiece by lazy { WordPiece(vocab.readLines(), MAX_TOKENS) }

    @Test
    fun `matches Python on every fixture text`() {
        assertTrue("run `uv run unstuk-export assets` in ml/", vocab.exists())
        assertTrue("run `uv run unstuk-token-fixture` in ml/", fixture.exists())
        val cases = fixture.readLines().map { Json.decodeFromString<Encoding>(it) }
        val wrong = cases.filter { case ->
            val got = wordPiece.encode(case.a, case.b)
            got.ids.toList() != case.ids || got.typeIds.toList() != case.typeIds
        }
        val first = wrong.take(3).joinToString(" | ") { it.a.take(80) }
        assertEquals("${wrong.size} of ${cases.size} differ, first: $first", 0, wrong.size)
    }

    @Test
    fun `a long pair is cut to the token limit with both sides kept`() {
        val long = List(200) { "phone" }.joinToString(" ")

        val tokens = wordPiece.encode(long, "do not disturb is on")

        assertEquals(MAX_TOKENS, tokens.ids.size)
        assertEquals(1L, tokens.typeIds.last())
    }
}
