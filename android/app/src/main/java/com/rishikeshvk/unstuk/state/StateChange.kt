package com.rishikeshvk.unstuk.state

import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.database.ContentObserver
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import androidx.core.content.ContextCompat
import kotlin.time.Duration
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withTimeoutOrNull

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
    context.contentResolver.registerContentObserver(
        Settings.Global.getUriFor(Settings.Global.AIRPLANE_MODE_ON),
        false,
        observer
    )
    ContextCompat.registerReceiver(
        context,
        receiver,
        IntentFilter(NotificationManager.ACTION_INTERRUPTION_FILTER_CHANGED),
        ContextCompat.RECEIVER_NOT_EXPORTED
    )
    // Read only after subscribing: a change landing between a read and the subscription would never be seen.
    trySend(Unit)
    awaitClose {
        context.contentResolver.unregisterContentObserver(observer)
        context.unregisterReceiver(receiver)
    }
}
