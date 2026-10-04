package com.rishikeshvk.unstuk.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.res.stringArrayResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.unit.dp
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.ui.motion.TypewriterHint

private val FieldShape = RoundedCornerShape(28.dp)

/**
 * Where the user says what's wrong. Empty, it types example complaints; [highlight] rings it in tangerine when
 * the app asks the user to try other words.
 */
@Composable
fun ComplaintField(
    value: String,
    onValueChange: (String) -> Unit,
    onSubmit: () -> Unit,
    modifier: Modifier = Modifier,
    highlight: Boolean = false
) {
    val colors = MaterialTheme.colorScheme
    val style = MaterialTheme.typography.bodyLarge.copy(color = colors.onSurface)
    val label = stringResource(R.string.complaint_label)
    BasicTextField(
        value = value,
        onValueChange = onValueChange,
        textStyle = style,
        cursorBrush = SolidColor(colors.tertiary),
        keyboardOptions = KeyboardOptions(
            capitalization = KeyboardCapitalization.Sentences,
            imeAction = ImeAction.Send
        ),
        keyboardActions = KeyboardActions(onSend = { onSubmit() }),
        minLines = 2,
        modifier = modifier
            .fillMaxWidth()
            .semantics { contentDescription = label },
        decorationBox = { field ->
            Box(
                Modifier
                    .fillMaxWidth()
                    .heightIn(min = 108.dp)
                    .background(colors.surface, FieldShape)
                    .border(2.dp, if (highlight) colors.tertiary else colors.onSurface, FieldShape)
                    .padding(horizontal = 20.dp, vertical = 18.dp)
            ) {
                if (value.isEmpty()) {
                    TypewriterHint(
                        examples = stringArrayResource(R.array.complaint_examples).toList(),
                        style = style,
                        color = colors.onSurfaceVariant
                    )
                }
                field()
            }
        }
    )
}
