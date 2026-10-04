package com.rishikeshvk.unstuk

import android.os.Build
import android.os.Bundle
import android.os.SystemClock
import android.view.View
import android.view.ViewTreeObserver
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.Composable
import androidx.lifecycle.viewmodel.compose.viewModel
import com.rishikeshvk.unstuk.catalog.CatalogLoader
import com.rishikeshvk.unstuk.fix.FixRunner
import com.rishikeshvk.unstuk.state.DeviceStateReader
import com.rishikeshvk.unstuk.trace.TraceWriter
import com.rishikeshvk.unstuk.ui.DebugScreen
import com.rishikeshvk.unstuk.ui.HelpViewModel
import com.rishikeshvk.unstuk.ui.UnstukApp
import com.rishikeshvk.unstuk.ui.theme.UnstukTheme
import java.io.File

// A beat after the line is complete, so the finished mark registers before Home appears.
private const val SPLASH_REST_MS = 300

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        if (savedInstanceState == null &&
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.S
        ) {
            holdSplash()
        }
        // The engineering screen ships in debug builds only; R8 drops it from release with the constant branch.
        val debugScreen: (@Composable () -> Unit)? = if (BuildConfig.DEBUG) debugScreen() else null
        setContent {
            UnstukTheme {
                UnstukApp(viewModel<HelpViewModel>(), debugScreen)
            }
        }
    }

    /**
     * The system splash leaves as soon as the first frame is ready, often before the Unknot has finished drawing.
     * Holding the first frame back keeps it up until the line is complete.
     */
    private fun holdSplash() {
        val until = SystemClock.uptimeMillis() +
            resources.getInteger(R.integer.splash_draw_ms) + SPLASH_REST_MS
        val content = findViewById<View>(android.R.id.content)
        content.viewTreeObserver.addOnPreDrawListener(
            object : ViewTreeObserver.OnPreDrawListener {
                override fun onPreDraw(): Boolean {
                    if (SystemClock.uptimeMillis() < until) return false
                    content.viewTreeObserver.removeOnPreDrawListener(this)
                    return true
                }
            }
        )
    }

    private fun debugScreen(): @Composable () -> Unit {
        val app = applicationContext
        val reader = DeviceStateReader(app)
        val catalog = CatalogLoader.load(app.assets)
        val runner = FixRunner(app)
        val traces = TraceWriter(File(app.filesDir, "traces"))
        return { DebugScreen(reader, catalog, runner, traces) }
    }
}
