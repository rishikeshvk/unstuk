package com.rishikeshvk.unstuk.ui.motion

import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import kotlinx.coroutines.delay

private const val TYPE_MS = 55L
private const val ERASE_MS = 25L
private const val HOLD_MS = 1600L
private const val CARET = "|"

/**
 * A placeholder that types example complaints one after another, showing that plain words work. It runs only
 * while the field is empty, since the field shows it only then.
 */
@Composable
fun TypewriterHint(examples: List<String>, style: TextStyle, color: Color) {
    if (rememberReducedMotion()) {
        Text(examples.first(), style = style, color = color)
        return
    }
    var shown by remember { mutableStateOf("") }
    LaunchedEffect(examples) {
        while (true) {
            for (example in examples) {
                for (end in 1..example.length) {
                    shown = example.take(end)
                    delay(TYPE_MS)
                }
                delay(HOLD_MS)
                for (end in example.length - 1 downTo 0) {
                    shown = example.take(end)
                    delay(ERASE_MS)
                }
            }
        }
    }
    Text(shown + CARET, style = style, color = color)
}
