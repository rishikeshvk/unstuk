package com.rishikeshvk.unstuk.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import com.rishikeshvk.unstuk.R

// Bundled subsets, not downloadable fonts: the app works with no network at all.
private val Bricolage = FontFamily(Font(R.font.bricolage_extrabold, FontWeight.ExtraBold))
private val Figtree = FontFamily(
    Font(R.font.figtree_regular, FontWeight.Normal),
    Font(R.font.figtree_semibold, FontWeight.SemiBold),
    Font(R.font.figtree_bold, FontWeight.Bold)
)

private val Headline = TextStyle(fontFamily = Bricolage, fontWeight = FontWeight.ExtraBold)
private val Body = TextStyle(fontFamily = Figtree, fontWeight = FontWeight.Normal)

val Typography = Typography(
    displaySmall = Headline.copy(fontSize = 38.sp, lineHeight = 40.sp, letterSpacing = (-0.03).em),
    headlineMedium = Headline.copy(
        fontSize = 30.sp,
        lineHeight = 32.sp,
        letterSpacing = (-0.02).em
    ),
    headlineSmall = Headline.copy(fontSize = 26.sp, lineHeight = 30.sp, letterSpacing = (-0.02).em),
    titleLarge = Body.copy(fontWeight = FontWeight.Bold, fontSize = 19.sp, lineHeight = 26.sp),
    titleMedium = Body.copy(fontWeight = FontWeight.SemiBold, fontSize = 17.sp, lineHeight = 22.sp),
    bodyLarge = Body.copy(fontSize = 18.sp, lineHeight = 26.sp),
    bodyMedium = Body.copy(fontSize = 16.sp, lineHeight = 22.sp),
    bodySmall = Body.copy(fontSize = 15.sp, lineHeight = 20.sp),
    labelLarge = Body.copy(
        fontWeight = FontWeight.Bold,
        fontSize = 15.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.02.em
    ),
    labelMedium = Body.copy(fontWeight = FontWeight.SemiBold, fontSize = 14.sp, lineHeight = 18.sp)
)
