package com.rishikeshvk.unstuk.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

// Fixed brand colours, no dynamic colour: a wallpaper must never turn the main button low-contrast.
// Roles: primary = ink (actions), tertiary = tangerine (found/done accents), tertiaryContainer = tint.
private val LightColors = lightColorScheme(
    primary = InkLight,
    onPrimary = Color.White,
    background = GroundLight,
    onBackground = InkLight,
    surface = SurfaceLight,
    onSurface = InkLight,
    onSurfaceVariant = MutedLight,
    tertiary = TangerineLight,
    onTertiary = Color.White,
    tertiaryContainer = TintLight,
    onTertiaryContainer = OnTintLight,
    outline = OutlineLight,
    outlineVariant = HairlineLight
)

private val DarkColors = darkColorScheme(
    primary = InkDark,
    onPrimary = GroundDark,
    background = GroundDark,
    onBackground = InkDark,
    surface = SurfaceDark,
    onSurface = InkDark,
    onSurfaceVariant = MutedDark,
    tertiary = TangerineDark,
    onTertiary = GroundDark,
    tertiaryContainer = TintDark,
    onTertiaryContainer = OnTintDark,
    outline = OutlineDark,
    outlineVariant = HairlineDark
)

private val UnstukShapes = Shapes(
    small = RoundedCornerShape(14.dp),
    medium = RoundedCornerShape(22.dp),
    large = RoundedCornerShape(24.dp),
    extraLarge = RoundedCornerShape(32.dp)
)

@Composable
fun UnstukTheme(darkTheme: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        typography = Typography,
        shapes = UnstukShapes,
        content = content
    )
}
