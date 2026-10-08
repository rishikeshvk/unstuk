package com.rishikeshvk.unstuk.decide

/** Token ids and segment ids for one encoder input, without padding. */
class Tokens(val ids: LongArray, val typeIds: LongArray)

/**
 * bge's tokenizer: BERT words, greedy longest-match WordPiece over [vocab] (one token per line, in id order),
 * `[CLS] a [SEP]` or `[CLS] a [SEP] b [SEP]`, truncated to [maxTokens] as Python's `tokenizers` does.
 */
class WordPiece(vocab: List<String>, private val maxTokens: Int) {
    private val ids = vocab.withIndex().associate { (id, token) -> token to id.toLong() }
    private val unknown = ids.getValue("[UNK]")
    private val cls = ids.getValue("[CLS]")
    private val sep = ids.getValue("[SEP]")

    fun encode(text: String, pair: String? = null): Tokens {
        var first = pieces(text)
        if (pair == null) {
            first = first.take(maxTokens - 2)
            val tokens = listOf(cls) + first + sep
            return Tokens(tokens.toLongArray(), LongArray(tokens.size))
        }
        var second = pieces(pair)
        val budget = maxTokens - 3
        if (first.size + second.size > budget) {
            // Longest first: the shorter side keeps up to half, ties counting the first as shorter.
            val firstShorter = first.size <= second.size
            val shorter = minOf(if (firstShorter) first.size else second.size, budget / 2)
            val longer = budget - shorter
            first = first.take(if (firstShorter) shorter else longer)
            second = second.take(if (firstShorter) longer else shorter)
        }
        val tokens = listOf(cls) + first + sep + second + sep
        val typeIds = LongArray(tokens.size) { if (it < first.size + 2) 0L else 1L }
        return Tokens(tokens.toLongArray(), typeIds)
    }

    private fun pieces(text: String): List<Long> = BertText.words(text).flatMap(::wordPieces)

    private fun wordPieces(word: String): List<Long> {
        val points = word.codePoints().toArray()
        if (points.size > MAX_WORD_CHARS) return listOf(unknown)
        val pieces = mutableListOf<Long>()
        var start = 0
        while (start < points.size) {
            val piece = longestPiece(points, start) ?: return listOf(unknown)
            pieces += piece.first
            start = piece.second
        }
        return pieces
    }

    /** The longest vocabulary piece starting at [start], and where it ends. */
    private fun longestPiece(points: IntArray, start: Int): Pair<Long, Int>? {
        for (end in points.size downTo start + 1) {
            val text = String(points, start, end - start)
            val id = ids[if (start > 0) "##$text" else text]
            if (id != null) return id to end
        }
        return null
    }

    private companion object {
        const val MAX_WORD_CHARS = 100
    }
}
