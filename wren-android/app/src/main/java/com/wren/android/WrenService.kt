package com.wren.android

import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat

class WrenService : Service() {

    override fun onCreate() {
        super.onCreate()
        ServerManager.resetState()
        startForeground(NOTIFICATION_ID, buildNotification("Wren AI preparing..."))
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> {
                ServerManager.start(
                    ctx = this,
                    scope = kotlinx.coroutines.CoroutineScope(kotlinx.coroutines.Dispatchers.Main),
                    onReady = {
                        val port = ServerManager.currentPort
                        updateNotification("Wren AI running on port $port")
                    },
                    onProgress = { updateNotification(it) },
                    onError = { msg ->
                        Log.e(TAG, "Server error: $msg")
                        updateNotification("Server error — tap to open")
                    }
                )
            }
            ACTION_STOP -> {
                ServerManager.stop()
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
            }
        }
        return START_STICKY
    }

    override fun onTaskRemoved(rootIntent: Intent?) {
        ServerManager.stop()
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
        super.onTaskRemoved(rootIntent)
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun buildNotification(msg: String = "Wren AI preparing..."): Notification {
        val openIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pending = PendingIntent.getActivity(
            this, 0, openIntent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        val stopIntent = Intent(this, WrenService::class.java).apply { action = ACTION_STOP }
        val stopPending = PendingIntent.getService(
            this, 1, stopIntent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        return NotificationCompat.Builder(this, WrenApp.CHANNEL_SERVER)
            .setContentTitle("Wren AI")
            .setContentText(msg)
            .setSmallIcon(android.R.drawable.ic_menu_compass)
            .setContentIntent(pending)
            .addAction(android.R.drawable.ic_media_pause, "Stop", stopPending)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE)
            .build()
    }

    private fun updateNotification(msg: String) {
        try {
            val manager = getSystemService(NOTIFICATION_SERVICE) as android.app.NotificationManager
            manager.notify(NOTIFICATION_ID, buildNotification(msg))
        } catch (e: Exception) {
            Log.e(TAG, "Failed to update notification", e)
        }
    }

    companion object {
        const val ACTION_START = "com.wren.android.START"
        const val ACTION_STOP = "com.wren.android.STOP"
        const val NOTIFICATION_ID = 1001
        private const val TAG = "WrenService"
    }
}
