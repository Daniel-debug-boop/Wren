package com.wren.android

import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat

class WrenService : Service() {
    override fun onCreate() {
        super.onCreate()
        startForeground(NOTIFICATION_ID, buildNotification())
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> ServerManager.start(this, onReady = {}, onProgress = { updateNotification(it) })
            ACTION_STOP -> { ServerManager.stop(); stopForeground(STOP_FOREGROUND_REMOVE); stopSelf() }
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?) = null

    private fun buildNotification(msg: String = "Wren AI preparing..."): Notification {
        val openIntent = Intent(this, MainActivity::class.java).apply { flags = Intent.FLAG_ACTIVITY_SINGLE_TOP }
        val pending = PendingIntent.getActivity(this, 0, openIntent, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        return NotificationCompat.Builder(this, WrenApp.CHANNEL_SERVER)
            .setContentTitle("Wren AI").setContentText(msg).setSmallIcon(android.R.drawable.ic_menu_compass)
            .setContentIntent(pending).setOngoing(true).setPriority(NotificationCompat.PRIORITY_LOW).build()
    }

    private fun updateNotification(msg: String) {
        (getSystemService(NOTIFICATION_SERVICE) as android.app.NotificationManager).notify(NOTIFICATION_ID, buildNotification(msg))
    }

    companion object {
        const val ACTION_START = "com.wren.android.START"
        const val ACTION_STOP = "com.wren.android.STOP"
        const val NOTIFICATION_ID = 1001
    }
}
