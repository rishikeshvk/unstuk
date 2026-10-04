package com.rishikeshvk.unstuk.debug

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.rishikeshvk.unstuk.catalog.CatalogLoader
import com.rishikeshvk.unstuk.fix.FixRunner
import com.rishikeshvk.unstuk.trace.TraceWriter
import com.rishikeshvk.unstuk.trace.Tracer
import java.io.File
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

private const val TAG = "TrialReceiver"

/** Lets the host-side trial runner run one fix: `am broadcast -a ...RUN_ACTION --es action <fix id> --es trialId <id>`. */
class TrialReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val app = context.applicationContext
        val catalog = CatalogLoader.load(app.assets)
        val fix = intent.getStringExtra("action")?.let { id ->
            catalog.fixes.firstOrNull {
                it.id ==
                    id
            }
        }
        val trialId = intent.getStringExtra("trialId")
        if (fix == null || trialId == null) {
            Log.w(TAG, "Ignoring broadcast without a known fix id and a trialId: ${intent.extras}")
            return
        }
        val pending = goAsync()
        CoroutineScope(Dispatchers.Default).launch {
            try {
                val tracer = Tracer(TraceWriter(File(app.filesDir, "traces")), trialId, fix.id)
                val outcome = FixRunner(app).run(fix, tracer)
                tracer.step("result", outcome.traceName, detail = outcome.reason)
            } catch (e: IllegalArgumentException) {
                Log.w(TAG, "Trial $trialId rejected", e)
            } finally {
                pending.finish()
            }
        }
    }
}
