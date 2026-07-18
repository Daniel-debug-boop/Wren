package com.wren.android

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context

class WrenApp : Application() {
    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
    }

    private fun createNotificationChannels() {
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(NotificationChannel(
            CHANNEL_SERVER, "Server Status", NotificationManager.IMPORTANCE_LOW
        ).apply { description = "Wren AI server running"; setShowBadge(false) })
        manager.createNotificationChannel(NotificationChannel(
            CHANNEL_JOBS, "Job Complete", NotificationManager.IMPORTANCE_HIGH
        ).apply { description = "Your project is ready"; enableVibration(true) })
    }

    companion object {
        const val CHANNEL_SERVER = "wren-server"
        const val CHANNEL_JOBS = "wren-jobs"

        private const val PREFS = "wren_prefs"
        private const val KEY_SETUP = "setup_done"

        fun isFirstRun(ctx: Context) =
            !ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean(KEY_SETUP, false)

        fun markSetupComplete(ctx: Context) =
            ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putBoolean(KEY_SETUP, true).apply()
    }
}
