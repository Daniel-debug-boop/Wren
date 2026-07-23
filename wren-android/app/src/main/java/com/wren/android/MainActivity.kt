package com.wren.android

import android.annotation.SuppressLint
import android.app.DownloadManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.view.ViewGroup
import android.webkit.*
import androidx.activity.ComponentActivity
import androidx.activity.OnBackPressedCallback
import androidx.activity.compose.setContent
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat

class MainActivity : ComponentActivity() {
    private var webView: WebView? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Request battery optimization exemption
        WrenUtils.requestBatteryOptimization(this)

        // Start foreground service
        startService(Intent(this, WrenService::class.java).apply { action = WrenService.ACTION_START })

        // Modern back navigation (replaces deprecated onBackPressed)
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView?.canGoBack() == true) webView?.goBack()
                else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })

        setContent {
            MaterialTheme(colorScheme = darkColorScheme()) {
                WrenMainScreen(
                    onJobComplete = { title, msg -> notifyJobComplete(title, msg) },
                    onWebViewCreated = { wv -> webView = wv },
                    onOpenSettings = { startActivity(Intent(this, SettingsActivity::class.java)) }
                )
            }
        }
    }

    override fun onDestroy() {
        webView?.destroy()
        webView = null
        super.onDestroy()
    }

    private fun notifyJobComplete(title: String, message: String) {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pending = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        try {
            NotificationManagerCompat.from(this).notify(
                WrenApp.NOTIFICATION_JOB_COMPLETE,
                NotificationCompat.Builder(this, WrenApp.CHANNEL_JOBS)
                    .setSmallIcon(android.R.drawable.ic_popup_reminder)
                    .setContentTitle(title)
                    .setContentText(message)
                    .setPriority(NotificationCompat.PRIORITY_HIGH)
                    .setAutoCancel(true)
                    .setContentIntent(pending)
                    .setVibrate(longArrayOf(0, 200, 100, 200))
                    .build()
            )
        } catch (_: SecurityException) {}
    }
}

// ── Main screen composable ─────────────────────────────────────────────────

@Composable
private fun WrenMainScreen(
    onJobComplete: (String, String) -> Unit,
    onWebViewCreated: (WebView) -> Unit,
    onOpenSettings: () -> Unit
) {
    val context = LocalContext.current
    var serverState by remember { mutableStateOf<ServerState>(ServerState.Starting) }
    var jobProgress by remember { mutableStateOf<Pair<String, Int>?>(null) }
    // Changing this value re-triggers server start (for retry)
    var retryTrigger by remember { mutableIntStateOf(0) }
    // Coroutine scope tied to composition lifecycle (no leak)
    val coroutineScope = rememberCoroutineScope()

    Box(Modifier.fillMaxSize().background(Color(0xFF0A0A0F))) {
        // WebView (hidden until server ready)
        AnimatedVisibility(visible = serverState is ServerState.Ready, enter = fadeIn(), exit = fadeOut()) {
            WrenWebView(
                onJobComplete = onJobComplete,
                onWebViewCreated = onWebViewCreated,
                onProgressUpdate = { stage, pct -> jobProgress = stage to pct }
            )
        }

        // Settings FAB (visible when server ready)
        if (serverState is ServerState.Ready) {
            FloatingActionButton(
                onClick = onOpenSettings,
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .padding(16.dp)
                    .size(48.dp),
                containerColor = Color(0xFF1A1A2E),
                contentColor = Color(0xFFC9B974)
            ) {
                Icon(Icons.Default.Settings, "Settings")
            }
        }

        // Overlay states
        when (val state = serverState) {
            is ServerState.Starting -> LoadingOverlay(
                message = state.message,
                progress = state.progress,
                isError = false,
                onRetry = null
            )
            is ServerState.Error -> LoadingOverlay(
                message = state.message,
                progress = null,
                isError = true,
                onRetry = { retryTrigger++ }
            )
            is ServerState.Ready -> {
                jobProgress?.let { (stage, pct) ->
                    JobProgressBanner(stage = stage, pct = pct)
                }
            }
        }
    }

    // Start server on first composition and on each retry
    LaunchedEffect(retryTrigger) {
        serverState = ServerState.Starting("Starting Wren AI...", 0f)
        ServerManager.start(
            ctx = context,
            scope = coroutineScope,
            onReady = { serverState = ServerState.Ready },
            onProgress = { msg ->
                val pct = when {
                    "Starting" in msg -> 0.2f
                    "Initializing" in msg -> 0.4f
                    "Waiting" in msg || "Connecting" in msg -> 0.7f
                    "ready" in msg.lowercase() -> 1.0f
                    else -> 0.5f
                }
                serverState = ServerState.Starting(msg, pct)
            },
            onError = { msg -> serverState = ServerState.Error(msg) }
        )
    }
}

// ── Server state sealed class ──────────────────────────────────────────────

private sealed class ServerState {
    data class Starting(val message: String, val progress: Float) : ServerState()
    data class Error(val message: String) : ServerState()
    data object Ready : ServerState()
}

// ── Loading / Error overlay ────────────────────────────────────────────────

@Composable
private fun LoadingOverlay(
    message: String,
    progress: Float?,
    isError: Boolean,
    onRetry: (() -> Unit)?
) {
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
            // Logo
            Text("W", fontSize = 72.sp, fontWeight = FontWeight.Bold, color = Color(0xFFC9B974))
            Spacer(Modifier.height(24.dp))
            Text("Wren AI", fontSize = 28.sp, fontWeight = FontWeight.SemiBold, color = Color.White)
            Spacer(Modifier.height(32.dp))

            if (progress != null && progress < 1.0f) {
                LinearProgressIndicator(
                    progress = { progress },
                    modifier = Modifier.fillMaxWidth(0.7f).height(4.dp).clip(RoundedCornerShape(2.dp)),
                    color = Color(0xFFC9B974),
                    trackColor = Color(0xFF2A2A35)
                )
            } else if (isError) {
                CircularProgressIndicator(
                    Modifier.size(32.dp),
                    color = MaterialTheme.colorScheme.error,
                    strokeWidth = 3.dp
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
                message,
                fontSize = 14.sp,
                color = if (isError) MaterialTheme.colorScheme.error else Color(0xFF888899),
                textAlign = TextAlign.Center
            )

            if (isError && onRetry != null) {
                Spacer(Modifier.height(24.dp))
                Button(
                    onClick = onRetry,
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFC9B974)),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("Retry", color = Color(0xFF0A0A0F), fontWeight = FontWeight.SemiBold)
                }
            }
        }
    }
}

// ── Job progress banner ────────────────────────────────────────────────────

@Composable
private fun JobProgressBanner(stage: String, pct: Int) {
    Box(
        Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
        contentAlignment = Alignment.TopCenter
    ) {
        Surface(
            color = Color(0xFF1A1A2E).copy(alpha = 0.95f),
            shape = RoundedCornerShape(12.dp),
            tonalElevation = 4.dp
        ) {
            Row(
                Modifier.padding(horizontal = 16.dp, vertical = 10.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                CircularProgressIndicator(
                    progress = { pct / 100f },
                    modifier = Modifier.size(16.dp),
                    strokeWidth = 2.dp,
                    color = Color(0xFFC9B974),
                    trackColor = Color(0xFF2A2A35)
                )
                Spacer(Modifier.width(12.dp))
                Text(
                    "$stage ($pct%)",
                    color = Color(0xFFCCCCCC),
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Medium
                )
            }
        }
    }
}

// ── WebView composable ─────────────────────────────────────────────────────

@SuppressLint("SetJavaScriptEnabled")
@Composable
private fun WrenWebView(
    onJobComplete: (String, String) -> Unit,
    onWebViewCreated: (WebView) -> Unit,
    onProgressUpdate: (String, Int) -> Unit
) {
    AndroidView(
        factory = { ctx ->
            WebView(ctx).apply {
                layoutParams = ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT
                )
                settings.apply {
                    javaScriptEnabled = true
                    domStorageEnabled = true
                    databaseEnabled = true
                    cacheMode = WebSettings.LOAD_DEFAULT
                    loadWithOverviewMode = true
                    useWideViewPort = true
                    builtInZoomControls = false
                    displayZoomControls = false
                    mediaPlaybackRequiresUserGesture = false

                    // Security hardening
                    mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
                    allowFileAccess = false
                    allowContentAccess = false
                    allowFileAccessFromFileURLs = false
                    allowUniversalAccessFromFileURLs = false
                    savePassword = false
                    saveFormData = false
                }

                // JS bridge with input sanitization
                addJavascriptInterface(object {
                    @JavascriptInterface
                    fun onJobReady(title: String, message: String) {
                        val safeTitle = title.take(200).replace(Regex("[\\x00-\\x1F\\x7F]"), "")
                        val safeMsg = message.take(500).replace(Regex("[\\x00-\\x1F\\x7F]"), "")
                        onJobComplete(safeTitle, safeMsg)
                    }

                    @JavascriptInterface
                    fun onJobProgress(stage: String, pct: Int) {
                        val safeStage = stage.take(100).replace(Regex("[\\x00-\\x1F\\x7F]"), "")
                        onProgressUpdate(safeStage, pct.coerceIn(0, 100))
                    }
                }, "WrenAndroid")

                webViewClient = object : WebViewClient() {
                    override fun onReceivedError(
                        view: WebView?, request: WebResourceRequest?, error: WebResourceError?
                    ) {
                        // Main frame errors handled by WrenMainScreen
                    }
                }

                // File download support
                setDownloadListener { url, _, _, mimeType, _ ->
                    if (url != null) {
                        val request = DownloadManager.Request(Uri.parse(url))
                            .setMimeType(mimeType)
                            .setNotificationVisibility(
                                DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED
                            )
                            .setDestinationInExternalPublicDir(
                                Environment.DIRECTORY_DOWNLOADS,
                                Uri.parse(url).lastPathSegment ?: "download"
                            )
                        val dm = ctx.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
                        dm.enqueue(request)
                    }
                }

                // Load from configured port (WrenSettings.PREFS_NAME = "wren_settings")
                val port = WrenSettings.getPort(ctx)
                loadUrl("http://127.0.0.1:$port/")
                onWebViewCreated(this)
            }
        },
        modifier = Modifier.fillMaxSize()
    )
}
