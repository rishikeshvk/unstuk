package com.rishikeshvk.unstuk.ui.reply

import androidx.compose.runtime.Composable
import com.rishikeshvk.unstuk.flow.FixStep
import com.rishikeshvk.unstuk.flow.Reply

/** One reply, one screen. A Run never shows here: the view model runs it and shows the working screen. */
@Composable
fun ReplyScreen(
    reply: Reply,
    complaint: String,
    fixed: Set<String>,
    howFixed: List<FixStep>,
    actions: ReplyActions
) {
    when (reply) {
        Reply.Decline -> DeclineReply(complaint, actions)
        is Reply.Clarify -> ClarifyReply(reply, complaint, actions)
        is Reply.Confirm -> ConfirmReply(reply, fixed, actions)
        is Reply.Run -> WorkingReply(reply.fix)
        is Reply.Fixed -> FixedReply(reply, fixed, howFixed, actions)
        is Reply.AlreadyFine -> AlreadyFineReply(reply, actions)
        is Reply.AllClear -> TipsReply(reply.intent, reply.scan, fixed, actions)
        is Reply.Guide -> GuideReply(reply, actions)
        Reply.NeedsUnlock -> UnlockReply(actions)
    }
}
