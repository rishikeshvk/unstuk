package com.rishikeshvk.unstuk.state

import android.os.Build

data class DeviceInfo(val make: String, val model: String, val sdk: Int, val build: String) {
    companion object {
        fun current() = DeviceInfo(
            make = Build.MANUFACTURER,
            model = Build.MODEL,
            sdk = Build.VERSION.SDK_INT,
            build = Build.DISPLAY
        )
    }
}
