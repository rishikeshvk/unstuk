package com.rishikeshvk.unstuk.ui.theme

import android.content.Context
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.Composable
import androidx.core.content.edit

/** The user's Appearance setting. */
enum class ThemeChoice {
    SYSTEM,
    LIGHT,
    DARK;

    @Composable
    fun isDark(): Boolean = when (this) {
        SYSTEM -> isSystemInDarkTheme()
        LIGHT -> false
        DARK -> true
    }
}

private const val PREFS = "settings"
private const val KEY_THEME = "theme"

/** Keeps the Appearance setting on the device, in the app's private preferences. */
class ThemeStore(context: Context) {
    private val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    fun load(): ThemeChoice = prefs.getString(KEY_THEME, null)
        ?.let { name -> ThemeChoice.entries.firstOrNull { it.name == name } }
        ?: ThemeChoice.SYSTEM

    fun save(choice: ThemeChoice) = prefs.edit { putString(KEY_THEME, choice.name) }
}
