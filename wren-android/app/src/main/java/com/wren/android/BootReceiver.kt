package com.wren.android

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/**
 * Auto-starts Wren server on phone boot.
 * User never needs to open Termux or tap anything.
 */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            val serviceIntent = Intent(context, WrenService::class.java).apply {
                action = WrenService.ACTION_START
            }
            context.startForegroundService(serviceIntent)
        }
    }
}
