package com.rishikeshvk.unstuk.decide

import java.text.Normalizer

/**
 * BERT's text clean-up and word split, as bge's `tokenizer.json` asks for (BertNormalizer, BertPreTokenizer):
 * drop control characters, space out CJK ideographs, strip accents, lowercase, then split on whitespace and
 * make every punctuation mark its own word. Works on code points, as the Rust original does on chars.
 */
object BertText {
    fun words(text: String): List<String> = split(normalize(text))

    private fun normalize(text: String): String {
        val cleaned = buildString {
            text.codePoints().forEach { c ->
                when {
                    c == 0 || c == 0xFFFD || isControl(c) -> Unit
                    isWhitespace(c) -> append(' ')
                    isCjk(c) -> append(' ').appendCodePoint(c).append(' ')
                    else -> appendCodePoint(c)
                }
            }
        }
        val stripped = Normalizer.normalize(cleaned, Normalizer.Form.NFD)
            .codePoints()
            .filter { Character.getType(it) != Character.NON_SPACING_MARK.toInt() }
            .collect(::StringBuilder, StringBuilder::appendCodePoint, StringBuilder::append)
            .toString()
        return stripped.lowercase()
    }

    private fun split(text: String): List<String> {
        val words = mutableListOf<String>()
        val word = StringBuilder()
        fun flush() {
            if (word.isNotEmpty()) words += word.toString()
            word.clear()
        }
        text.codePoints().forEach { c ->
            when {
                isWhitespace(c) -> flush()
                isPunctuation(c) -> {
                    flush()
                    words += String(Character.toChars(c))
                }
                else -> word.appendCodePoint(c)
            }
        }
        flush()
        return words
    }

    private fun isWhitespace(c: Int) =
        c in ASCII_WHITESPACE || Character.isWhitespace(c) || Character.isSpaceChar(c)

    private fun isControl(c: Int) = c !in ASCII_WHITESPACE && Character.getType(c) in CONTROL_TYPES

    private fun isPunctuation(c: Int) =
        ASCII_PUNCTUATION.any { c in it } || Character.getType(c) in PUNCTUATION_TYPES

    private fun isCjk(c: Int) = CJK.any { c in it }

    private val ASCII_WHITESPACE = setOf(' '.code, '\t'.code, '\n'.code, '\r'.code)
    private val ASCII_PUNCTUATION = listOf(33..47, 58..64, 91..96, 123..126)
    private val CONTROL_TYPES = setOf(
        Character.CONTROL,
        Character.FORMAT,
        Character.UNASSIGNED,
        Character.PRIVATE_USE
    ).map(Byte::toInt)
    private val PUNCTUATION_TYPES = setOf(
        Character.CONNECTOR_PUNCTUATION,
        Character.DASH_PUNCTUATION,
        Character.START_PUNCTUATION,
        Character.END_PUNCTUATION,
        Character.INITIAL_QUOTE_PUNCTUATION,
        Character.FINAL_QUOTE_PUNCTUATION,
        Character.OTHER_PUNCTUATION
    ).map(Byte::toInt)

    // The CJK Unified Ideographs blocks BERT spaces out; Hangul and kana are not among them.
    private val CJK = listOf(
        0x4E00..0x9FFF,
        0x3400..0x4DBF,
        0x20000..0x2A6DF,
        0x2A700..0x2B73F,
        0x2B740..0x2B81F,
        0x2B820..0x2CEAF,
        0xF900..0xFAFF,
        0x2F800..0x2FA1F
    )
}
