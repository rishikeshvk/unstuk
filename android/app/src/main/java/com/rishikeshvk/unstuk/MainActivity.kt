package com.rishikeshvk.unstuk

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.annotation.StringRes
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.PrimaryTabRow
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import com.rishikeshvk.unstuk.catalog.CatalogLoader
import com.rishikeshvk.unstuk.fix.FixRunner
import com.rishikeshvk.unstuk.flow.ComplaintFlow
import com.rishikeshvk.unstuk.state.DeviceStateReader
import com.rishikeshvk.unstuk.trace.TraceWriter
import com.rishikeshvk.unstuk.ui.ComplaintScreen
import com.rishikeshvk.unstuk.ui.DebugScreen
import com.rishikeshvk.unstuk.ui.SetupScreen
import com.rishikeshvk.unstuk.ui.theme.UnstukTheme
import java.io.File

private enum class Tab(@StringRes val title: Int) {
    HELP(R.string.tab_help),
    SETUP(R.string.tab_setup),
    DEBUG(R.string.tab_debug)
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val app = applicationContext
        val flow = ComplaintFlow(app)
        val reader = DeviceStateReader(app)
        val catalog = CatalogLoader.load(app.assets)
        val runner = FixRunner(app)
        val traces = TraceWriter(File(app.filesDir, "traces"))
        setContent {
            UnstukTheme {
                var tab by rememberSaveable { mutableIntStateOf(0) }
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    Column(Modifier.padding(innerPadding)) {
                        PrimaryTabRow(selectedTabIndex = tab) {
                            Tab.entries.forEach { entry ->
                                Tab(
                                    selected = tab == entry.ordinal,
                                    onClick = { tab = entry.ordinal },
                                    text = { Text(stringResource(entry.title)) }
                                )
                            }
                        }
                        when (Tab.entries[tab]) {
                            Tab.HELP -> ComplaintScreen(flow)
                            Tab.SETUP -> SetupScreen()
                            Tab.DEBUG -> DebugScreen(reader, catalog, runner, traces)
                        }
                    }
                }
            }
        }
    }
}
