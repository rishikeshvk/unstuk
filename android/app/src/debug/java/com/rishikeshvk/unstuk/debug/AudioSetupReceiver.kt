package com.rishikeshvk.unstuk.debug

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.media.AudioManager
import android.util.Log

private const val TAG = "AudioSetupReceiver"

/**
 * Puts audio in a broken state for the host scripts, because the shell's volume command is ignored on the Moto:
 * `am broadcast -a ...SET_AUDIO --ei stream <n> --ei index <i>` or `--ei ringer <mode>`.
 */
class AudioSetupReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val audio = context.getSystemService(AudioManager::class.java)
        try {
            if (intent.hasExtra("ringer")) {
                audio.ringerMode = intent.getIntExtra("ringer", AudioManager.RINGER_MODE_NORMAL)
            }
            if (intent.hasExtra("stream")) {
                audio.setStreamVolume(
                    intent.getIntExtra("stream", -1),
                    intent.getIntExtra("index", 0),
                    0
                )
            }
        } catch (e: SecurityException) {
            Log.w(TAG, "Audio change refused", e)
        }
    }
}
