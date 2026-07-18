package com.wren.android

import android.annotation.SuppressLint
import android.app.PendingIntent
import android.content.Intent
import android.graphics.Bitmap
import android.os.Bundle
import android.view.ViewGroup
import android.webkit.*
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat

class MainActivity : ComponentActivity() {
    private var webView: WebView? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        startService(Intent(this, WrenService::class.java).apply { action = WrenService.ACTION_START })

        setContent {
            WrenWebView(
                onJobComplete = { title, msg -> notifyJobComplete(title, msg) },
                onWebViewCreated = { wv -> webView = wv }
            )
        }
    }

    override fun onBackPressed() {
        if (webView?.canGoBack() == true) webView?.goBack() else super.onBackPressed()
    }

    override fun onDestroy() { webView?.destroy(); super.onDestroy() }

    private fun notifyJobComplete(title: String, message: String) {
        val intent = Intent(this, MainActivity::class.java).apply { flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP }
        val pending = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        try {
            NotificationManagerCompat.from(this).notify(1002,
                NotificationCompat.Builder(this, WrenApp.CHANNEL_JOBS)
                    .setSmallIcon(android.R.drawable.ic_popup_reminder).setContentTitle(title).setContentText(message)
                    .setPriority(NotificationCompat.PRIORITY_HIGH).setAutoCancel(true).setContentIntent(pending)
                    .setVibrate(longArrayOf(0, 200, 100, 200)).build())
        } catch (_: SecurityException) {}
    }
}

@SuppressLint("SetJavaScriptEnabled")
@Composable
private fun WrenWebView(onJobComplete: (String, String) -> Unit, onWebViewCreated: (WebView) -> Unit) {
    var loading by remember { mutableStateOf(true) }
    var loadError by remember { mutableStateOf(false) }

    Box(Modifier.fillMaxSize()) {
        AndroidView(factory = { ctx ->
            WebView(ctx).apply {
                layoutParams = ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
                settings.apply {
                    javaScriptEnabled = true; domStorageEnabled = true; databaseEnabled = true
                    cacheMode = WebSettings.LOAD_DEFAULT; loadWithOverviewMode = true; useWideViewPort = true
                    builtInZoomControls = false; displayZoomControls = false; mediaPlaybackRequiresUserGesture = false
                    mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
                }
                addJavascriptInterface(object {
                    @JavascriptInterface fun onJobReady(title: String, message: String) = onJobComplete(title, message)
                    @JavascriptInterface fun onJobProgress(stage: String, pct: Int) {}
                }, "WrenAndroid")
                webViewClient = object : WebViewClient() {
                    override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) { loading = true; loadError = false }
                    override fun onPageFinished(view: WebView?, url: String?) { loading = false }
                    override fun onReceivedError(view: WebView?, request: WebResourceRequest?, error: WebResourceError?) { loadError = true; loading = false }
                }
                webChromeClient = WebChromeClient()
                loadUrl("http://127.0.0.1:${ServerManager.PORT}/")
                onWebViewCreated(this)
            }
        }, modifier = Modifier.fillMaxSize())

        if (loading) {
            Surface(color = Color(0xFF0A0A0F), modifier = Modifier.fillMaxSize()) {
                Column(Modifier.fillMaxSize(), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
                    CircularProgressIndicator(color = Color(0xFFC9B974), strokeWidth = 3.dp, modifier = Modifier.size(28.dp))
                    Spacer(Modifier.height(16.dp))
                    Text(if (loadError) "Starting server..." else "Wren AI", color = if (loadError) Color(0xFF888899) else Color.White, fontWeight = FontWeight.SemiBold, fontSize = 18.sp)
                }
            }
        }
    }
}
