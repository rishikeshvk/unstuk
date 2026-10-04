package com.rishikeshvk.unstuk.state

/** A stream volume as the device reports it: an index from 0 to [max], whose scale differs between phones. */
data class Volume(val level: Int, val max: Int)
