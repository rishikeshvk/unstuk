package com.rishikeshvk.unstuk.debug

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.rishikeshvk.unstuk.flow.ComplaintFlow
import com.rishikeshvk.unstuk.flow.Reply
import com.rishikeshvk.unstuk.trace.TraceWriter
import com.rishikeshvk.unstuk.trace.Tracer
import java.io.File
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

private const val TAG = "ComplaintReceiver"

/**
 * Runs the whole pipeline for the e2e runner, standing in for the user's taps:
 * `am broadcast -a ...RUN_COMPLAINT --es complaint <text> --es trialId <id> [--ez confirm true] [--es choose <intent>]`.
 * The trace ends with a `result` line naming the last reply.
 */
class ComplaintReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val complaint = intent.getStringExtra("complaint")
        val trialId = intent.getStringExtra("trialId")
        if (complaint == null || trialId == null) {
            Log.w(TAG, "Ignoring broadcast without a complaint and a trialId: ${intent.extras}")
            return
        }
        val confirm = intent.getBooleanExtra("confirm", false)
        val choose = intent.getStringExtra("choose")
        val app = context.applicationContext
        val pending = goAsync()
        CoroutineScope(Dispatchers.Default).launch {
            try {
                val flow = ComplaintFlow(app)
                var reply = flow.start(complaint, trialId)
                if (reply is Reply.Clarify && choose != null) reply = flow.choose(choose, trialId)
                reply = when {
                    reply is Reply.Run -> flow.run(
                        reply.intent.id,
                        reply.fix.id,
                        reply.confidence,
                        trialId
                    )
                    reply is Reply.Confirm && confirm ->
                        flow.run(reply.intent.id, reply.fix.id, reply.confidence, trialId)
                    else -> reply
                }
                Tracer(TraceWriter(File(app.filesDir, "traces")), trialId, "complaint")
                    .step("result", reply.traceName)
            } catch (e: IllegalArgumentException) {
                Log.w(TAG, "Complaint $trialId rejected", e)
            } finally {
                pending.finish()
            }
        }
    }
}
