package com.rishikeshvk.unstuk.debug

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.provider.Settings
import android.util.Log
import com.rishikeshvk.unstuk.a11y.NodeFinder
import com.rishikeshvk.unstuk.a11y.QuickSettings
import com.rishikeshvk.unstuk.a11y.UnstukService
import com.rishikeshvk.unstuk.selector.SelectorLoader
import java.io.File
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

private const val TAG = "LabelDumpReceiver"
private const val QUICK_SETTINGS = "qs"

/** The Settings screens dumped for the node-label test, by the name the script passes. */
private val SETTINGS_SCREENS = mapOf(
    "network" to Settings.ACTION_WIRELESS_SETTINGS,
    "bluetooth" to Settings.ACTION_BLUETOOTH_SETTINGS,
    "sound" to Settings.ACTION_SOUND_SETTINGS,
    "dnd" to "android.settings.ZEN_MODE_SETTINGS",
    "display" to Settings.ACTION_DISPLAY_SETTINGS,
    "accessibility" to Settings.ACTION_ACCESSIBILITY_SETTINGS,
    "date_time" to Settings.ACTION_DATE_SETTINGS
)

@Serializable
data class LabelDump(
    val screen: String,
    val manufacturer: String,
    val model: String,
    val sdk: Int,
    val nodes: List<DumpedNode>
)

/**
 * Dumps the labels on one screen for the node-label test set: `am broadcast -a ...DUMP_LABELS --es screen <name>`,
 * names `qs` or a key of [SETTINGS_SCREENS]. Writes `files/labels/<name>.json`. Never `uiautomator dump` (M1 rule).
 */
class LabelDumpReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val screen = intent.getStringExtra("screen")
        val service = UnstukService.connected.value
        if (screen == null ||
            (screen != QUICK_SETTINGS && screen !in SETTINGS_SCREENS) ||
            service == null
        ) {
            Log.w(
                TAG,
                "Needs a known screen and a bound service: screen=$screen bound=${service != null}"
            )
            return
        }
        val app = context.applicationContext
        val selectors = SelectorLoader.load(app.assets, Build.MANUFACTURER)
        val pending = goAsync()
        CoroutineScope(Dispatchers.Default).launch {
            try {
                val labels = ScreenLabels(service)
                val nodes = if (screen == QUICK_SETTINGS) {
                    labels.quickSettings(
                        selectors.quickSettings.packageName,
                        selectors.quickSettings.pagerIds
                    ).also {
                        QuickSettings(service, selectors.quickSettings, NodeFinder(service)).close()
                    }
                } else {
                    labels.settings(
                        selectors.settings.packageName,
                        SETTINGS_SCREENS.getValue(screen)
                    )
                }
                val dump =
                    LabelDump(screen, Build.MANUFACTURER, Build.MODEL, Build.VERSION.SDK_INT, nodes)
                val file = File(app.filesDir, "labels/$screen.json")
                file.parentFile?.mkdirs()
                file.writeText(Json.encodeToString(dump))
                Log.i(TAG, "Dumped ${nodes.size} nodes from $screen")
            } finally {
                pending.finish()
            }
        }
    }
}
