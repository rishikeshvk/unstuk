package com.rishikeshvk.unstuk

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.ui.Modifier
import com.rishikeshvk.unstuk.action.ActionRunner
import com.rishikeshvk.unstuk.state.DeviceStateReader
import com.rishikeshvk.unstuk.ui.DebugScreen
import com.rishikeshvk.unstuk.ui.theme.UnstukTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val reader = DeviceStateReader(applicationContext)
        val runner = ActionRunner(applicationContext)
        setContent {
            UnstukTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    DebugScreen(reader, runner, Modifier.padding(innerPadding))
                }
            }
        }
    }
}
