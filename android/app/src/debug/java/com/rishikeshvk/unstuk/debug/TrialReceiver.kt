package com.rishikeshvk.unstuk.debug

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.rishikeshvk.unstuk.action.ActionRunner
import com.rishikeshvk.unstuk.action.UnstukAction
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

private const val TAG = "TrialReceiver"

/** Lets the host-side trial runner start an action: `am broadcast -a ...RUN_ACTION --es action <name> --es trialId <id>`. */
class TrialReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.getStringExtra("action")?.let(UnstukAction::fromTraceName)
        val trialId = intent.getStringExtra("trialId")
        if (action == null || trialId == null) {
            Log.w(TAG, "Ignoring broadcast without a known action and a trialId: ${intent.extras}")
            return
        }
        val pending = goAsync()
        CoroutineScope(Dispatchers.Default).launch {
            try {
                ActionRunner(context.applicationContext).run(action, trialId)
            } catch (e: IllegalArgumentException) {
                Log.w(TAG, "Trial $trialId rejected", e)
            } finally {
                pending.finish()
            }
        }
    }
}
