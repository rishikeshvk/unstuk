package com.rishikeshvk.unstuk.ui.reply

import com.rishikeshvk.unstuk.catalog.Area
import com.rishikeshvk.unstuk.catalog.FixEntry
import com.rishikeshvk.unstuk.catalog.IntentEntry
import com.rishikeshvk.unstuk.flow.Reply

/** Everything a reply screen can ask for, so the screens stay free of the view model and easy to preview. */
class ReplyActions(
    val back: () -> Unit,
    val finish: () -> Unit,
    val updateComplaint: (String) -> Unit,
    val submit: () -> Unit,
    val openTopic: (Area) -> Unit,
    val pick: (String) -> Unit,
    val noneOfThese: () -> Unit,
    val confirm: (intentId: String, fix: FixEntry, confidence: Double) -> Unit,
    val retry: () -> Unit,
    val recheck: (Reply.Guide) -> Unit,
    val showTips: (IntentEntry) -> Unit,
    val showReply: (Reply) -> Unit
)
