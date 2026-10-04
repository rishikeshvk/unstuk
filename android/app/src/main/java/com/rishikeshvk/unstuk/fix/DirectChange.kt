package com.rishikeshvk.unstuk.fix

import android.content.Context

/** A system API call that makes the change itself. It is available only with [grant], and up to [maxSdk]. */
class DirectChange(val grant: Grant?, val maxSdk: Int = Int.MAX_VALUE, val apply: (Context) -> Unit)
