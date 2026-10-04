package com.rishikeshvk.unstuk

import android.os.Bundle
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

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        // The engineering screen ships in debug builds only; R8 drops it from release with the constant branch.
        val debugScreen: (@Composable () -> Unit)? = if (BuildConfig.DEBUG) debugScreen() else null
        setContent {
            UnstukTheme {
                UnstukApp(viewModel<HelpViewModel>(), debugScreen)
            }
        }
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
