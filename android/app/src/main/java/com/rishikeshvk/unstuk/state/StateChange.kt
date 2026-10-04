package com.rishikeshvk.unstuk.state

import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.database.ContentObserver
import android.media.AudioManager
import android.net.ConnectivityManager
import android.net.wifi.WifiManager
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import androidx.core.content.ContextCompat
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull

// Some state (mobile data, validated internet) changes without a settings write or a broadcast we can receive.
private val POLL_INTERVAL = 500.milliseconds

private val SETTINGS_TABLES = listOf(
    Settings.Global.CONTENT_URI,
    Settings.System.CONTENT_URI,
    Settings.Secure.CONTENT_URI
)

private val BROADCASTS = IntentFilter().apply {
    addAction(NotificationManager.ACTION_INTERRUPTION_FILTER_CHANGED)
    addAction(AudioManager.RINGER_MODE_CHANGED_ACTION)
    addAction(WifiManager.WIFI_STATE_CHANGED_ACTION)
    addAction(ConnectivityManager.ACTION_RESTRICT_BACKGROUND_CHANGED)
}

/**
 * Waits until [predicate] holds for a fresh read, or [timeout] passes (null). Observers only say when to look
 * again; the answer always comes from [DeviceStateReader.read].
 */
suspend fun awaitState(
    context: Context,
    reader: DeviceStateReader,
    timeout: Duration,
    predicate: (DeviceState) -> Boolean
): DeviceState? = withTimeoutOrNull(timeout) {
    stateChanges(context).map { reader.read() }.first(predicate)
}

// Watches whole settings tables rather than per-predicate keys: an extra wake-up costs one read, a missed one a
// false timeout.
private fun stateChanges(context: Context) = callbackFlow {
    val observer = object : ContentObserver(Handler(Looper.getMainLooper())) {
        override fun onChange(selfChange: Boolean) {
            trySend(Unit)
        }
    }
    val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            trySend(Unit)
        }
    }
    SETTINGS_TABLES.forEach { context.contentResolver.registerContentObserver(it, true, observer) }
    ContextCompat.registerReceiver(
        context,
        receiver,
        BROADCASTS,
        ContextCompat.RECEIVER_NOT_EXPORTED
    )
    // Read only after subscribing: a change landing between a read and the subscription would never be seen.
    trySend(Unit)
    val poller = launch {
        while (true) {
            delay(POLL_INTERVAL)
            trySend(Unit)
        }
    }
    awaitClose {
        poller.cancel()
        context.contentResolver.unregisterContentObserver(observer)
        context.unregisterReceiver(receiver)
    }
}
