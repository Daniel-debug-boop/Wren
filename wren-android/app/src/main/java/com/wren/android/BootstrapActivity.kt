package com.wren.android

import android.Manifest
import android.app.PendingIntent
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import kotlinx.coroutines.delay

class BootstrapActivity : ComponentActivity() {
    private val isFirstRun: Boolean get() = WrenApp.isFirstRun(this)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (Build.VERSION.SDK_INT >= 33) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 0)
        }

        setContent {
            BootstrapScreen(
                isFirstRun = isFirstRun,
                onComplete = {
                    WrenApp.markSetupComplete(this)
                    startActivity(Intent(this, MainActivity::class.java))
                    finish()
                }
            )
        }
    }
}

@Composable
private fun BootstrapScreen(isFirstRun: Boolean, onComplete: () -> Unit) {
    var phase by remember { mutableStateOf(if (isFirstRun) "Setting up Wren AI..." else "Starting...") }
    var progress by remember { mutableFloatStateOf(0f) }

    val infiniteTransition = rememberInfiniteTransition()
    val alpha by infiniteTransition.animateFloat(0.6f, 1.0f, infiniteRepeatable(tween(1500, easing = EaseInOutCubic), RepeatMode.Reverse))

    LaunchedEffect(isFirstRun) {
        if (isFirstRun) {
            for ((msg, pct) in listOf(
                "Setting up Python runtime..." to 0.1f, "Installing server packages..." to 0.3f,
                "Extracting Wren AI engine..." to 0.5f, "Configuring web server..." to 0.7f,
                "Finalizing setup..." to 0.9f, "Ready!" to 1.0f
            )) { phase = msg; progress = pct; delay(800) }
            delay(500)
        } else {
            delay(1200)
        }
        onComplete()
    }

    Box(Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(Color(0xFF0A0A0F), Color(0xFF12121A)))), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.padding(32.dp)) {
            Text("W", fontSize = 72.sp, fontWeight = FontWeight.Bold, color = Color(0xFFC9B974), modifier = Modifier.alpha(alpha))
            Spacer(Modifier.height(24.dp))
            Text("Wren AI", fontSize = 28.sp, fontWeight = FontWeight.SemiBold, color = Color.White)
            Spacer(Modifier.height(32.dp))
            if (isFirstRun) {
                LinearProgressIndicator(progress = { progress }, modifier = Modifier.fillMaxWidth(0.7f).height(4.dp), color = Color(0xFFC9B974), trackColor = Color(0xFF2A2A35))
            } else {
                CircularProgressIndicator(Modifier.size(32.dp), color = Color(0xFFC9B974), strokeWidth = 3.dp)
            }
            Spacer(Modifier.height(16.dp))
            Text(phase, fontSize = 14.sp, color = Color(0xFF888899), textAlign = TextAlign.Center)
        }
    }
}
