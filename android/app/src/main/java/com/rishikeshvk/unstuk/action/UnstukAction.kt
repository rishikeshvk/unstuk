package com.rishikeshvk.unstuk.action

/** The actions M1 can run. [traceName] is the stable name used in traces and by the trial runner. */
enum class UnstukAction(val traceName: String) {
    AIRPLANE_MODE_OFF("airplane_off"),
    DND_OFF("dnd_off")
    ;

    companion object {
        fun fromTraceName(name: String) = entries.firstOrNull { it.traceName == name }
    }
}
