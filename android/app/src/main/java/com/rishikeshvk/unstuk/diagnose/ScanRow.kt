package com.rishikeshvk.unstuk.diagnose

import com.rishikeshvk.unstuk.catalog.FixEntry

/** One cause of an intent as a snapshot found it: [holds] means [fix] is needed. */
data class ScanRow(val fix: FixEntry, val holds: Boolean)
