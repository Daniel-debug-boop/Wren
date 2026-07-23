package com.wren.android

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import kotlinx.coroutines.delay

class BootstrapActivity : ComponentActivity() {

    private val notificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { /* granted or denied — proceed either way */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Request notification permission on Android 13+
        if (Build.VERSION.SDK_INT >= 33) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) {
                notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }

        // Request battery optimization exemption
        WrenUtils.requestBatteryOptimization(this)

        val isFirstRun = WrenApp.isFirstRun(this)

        setContent {
            MaterialTheme(colorScheme = darkColorScheme()) {
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
}

@Composable
private fun BootstrapScreen(isFirstRun: Boolean, onComplete: () -> Unit) {
    val context = LocalContext.current
    var phase by remember { mutableStateOf(if (isFirstRun) "Setting up Wren AI..." else "Starting...") }
    var progress by remember { mutableFloatStateOf(0f) }
    var hasNetwork by remember { mutableStateOf(WrenUtils.isNetworkAvailable(context)) }

    // Re-check network on resume
    val lifecycleOwner = LocalLifecycleOwner.current
    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) {
                hasNetwork = WrenUtils.isNetworkAvailable(context)
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }

    val infiniteTransition = rememberInfiniteTransition()
    val alpha by infiniteTransition.animateFloat(
        0.6f, 1.0f,
        infiniteRepeatable(tween(1500, easing = EaseInOutCubic), RepeatMode.Reverse)
    )

    LaunchedEffect(isFirstRun) {
        if (isFirstRun) {
            val phases = listOf(
                "Setting up Python runtime..." to 0.15f,
                "Installing server packages..." to 0.35f,
                "Extracting Wren AI engine..." to 0.55f,
                "Configuring web server..." to 0.75f,
                "Finalizing setup..." to 0.90f,
                "Ready!" to 1.0f
            )
            for ((msg, pct) in phases) {
                phase = msg
                progress = pct
                delay(600)
            }
        } else {
            phase = "Starting server..."
            progress = 0.3f
            delay(400)
            phase = "Loading interface..."
            progress = 0.7f
            delay(400)
            phase = "Ready!"
            progress = 1.0f
        }
        delay(300)
        onComplete()
    }

    Box(
        Modifier.fillMaxSize().background(
            Brush.verticalGradient(listOf(Color(0xFF0A0A0F), Color(0xFF12121A)))
        ),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(32.dp)
        ) {
            Text(
                "W",
                fontSize = 72.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFFC9B974),
                modifier = Modifier.alpha(alpha)
            )
            Spacer(Modifier.height(24.dp))
            Text(
                "Wren AI",
                fontSize = 28.sp,
                fontWeight = FontWeight.SemiBold,
                color = Color.White
            )
            Spacer(Modifier.height(8.dp))
            Text(
                "Your AI software engineer",
                fontSize = 14.sp,
                color = Color(0xFF666677)
            )
            Spacer(Modifier.height(32.dp))

            if (isFirstRun) {
                LinearProgressIndicator(
                    progress = { progress },
                    modifier = Modifier
                        .fillMaxWidth(0.7f)
                        .height(4.dp)
                        .background(Color(0xFF2A2A35), RoundedCornerShape(2.dp)),
                    color = Color(0xFFC9B974),
                    trackColor = Color(0xFF2A2A35)
                )
            } else {
                CircularProgressIndicator(
                    Modifier.size(32.dp),
                    color = Color(0xFFC9B974),
                    strokeWidth = 3.dp
                )
            }

            Spacer(Modifier.height(16.dp))
            Text(
                phase,
                fontSize = 14.sp,
                color = Color(0xFF888899),
                textAlign = TextAlign.Center
            )

            if (!hasNetwork) {
                Spacer(Modifier.height(16.dp))
                Text(
                    "No internet connection. Some features may be limited.",
                    fontSize = 12.sp,
                    color = Color(0xFFCC6666),
                    textAlign = TextAlign.Center
                )
            }
        }
    }
}
