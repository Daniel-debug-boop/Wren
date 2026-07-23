package com.wren.android

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.util.Log

class WrenApp : Application() {

    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()

        // Crash recovery: reset server state if app was killed
        ServerManager.resetState()
    }

    private fun createNotificationChannels() {
        val manager = getSystemService(NotificationManager::class.java)

        // Server status channel (low priority, ongoing)
        manager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_SERVER,
                "Server Status",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Wren AI server status"
                setShowBadge(false)
            }
        )

        // Job complete channel (high priority, with vibration)
        manager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_JOBS,
                "Job Complete",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Your project is ready"
                enableVibration(true)
                vibrationPattern = longArrayOf(0, 200, 100, 200)
            }
        )
    }

    companion object {
        const val CHANNEL_SERVER = "wren-server"
        const val CHANNEL_JOBS = "wren-jobs"
        const val NOTIFICATION_JOB_COMPLETE = 1002

        private const val PREFS = "wren_prefs"
        private const val KEY_SETUP = "setup_done"

        fun isFirstRun(ctx: Context): Boolean =
            !ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean(KEY_SETUP, false)

        fun markSetupComplete(ctx: Context) {
            ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().putBoolean(KEY_SETUP, true).apply()
        }
    }
}
