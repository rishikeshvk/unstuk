package com.rishikeshvk.unstuk

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.ui.Modifier
import com.rishikeshvk.unstuk.catalog.CatalogLoader
import com.rishikeshvk.unstuk.fix.FixRunner
import com.rishikeshvk.unstuk.state.DeviceStateReader
import com.rishikeshvk.unstuk.trace.TraceWriter
import com.rishikeshvk.unstuk.ui.DebugScreen
import com.rishikeshvk.unstuk.ui.theme.UnstukTheme
import java.io.File

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val app = applicationContext
        val reader = DeviceStateReader(app)
        val catalog = CatalogLoader.load(app.assets)
        val runner = FixRunner(app)
        val traces = TraceWriter(File(app.filesDir, "traces"))
        setContent {
            UnstukTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    DebugScreen(reader, catalog, runner, traces, Modifier.padding(innerPadding))
                }
            }
        }
    }
}
