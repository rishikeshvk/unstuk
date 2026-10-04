package com.rishikeshvk.unstuk.ui.components

import androidx.annotation.DrawableRes
import androidx.annotation.StringRes
import com.rishikeshvk.unstuk.R
import com.rishikeshvk.unstuk.catalog.Area

/** How a topic looks on screen: its name and icon. */
@get:StringRes
val Area.title: Int
    get() = when (this) {
        Area.INTERNET -> R.string.area_internet
        Area.CALLS -> R.string.area_calls
        Area.SCREEN -> R.string.area_screen
        Area.MESSAGES -> R.string.area_messages
        Area.BLUETOOTH -> R.string.area_bluetooth
        Area.APPS -> R.string.area_apps
    }

@get:DrawableRes
val Area.icon: Int
    get() = when (this) {
        Area.INTERNET -> R.drawable.ic_area_internet
        Area.CALLS -> R.drawable.ic_area_calls
        Area.SCREEN -> R.drawable.ic_area_screen
        Area.MESSAGES -> R.drawable.ic_area_messages
        Area.BLUETOOTH -> R.drawable.ic_area_bluetooth
        Area.APPS -> R.drawable.ic_area_apps
    }
