package com.wren.android

import android.content.Context
import android.util.Log
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlinx.coroutines.*
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

object ServerManager {
    const val PORT = 12000  // Default port, used by MainActivity for initial loadUrl
    private const val MAX_RETRIES = 10
    private const val RETRY_DELAY_MS = 1000L
    private const val TAG = "WrenServer"

    @Volatile
    private var running = false
    private var serverJob: Job? = null

    /** Current port (may differ from default if user changed it in settings). */
    @Volatile
    var currentPort: Int = PORT
        private set

    /** Health check URL derived from current port. */
    private val healthUrl: String get() = "http://127.0.0.1:$currentPort/api/health"

    /**
     * Start the Python server with health-check polling and retry.
     * Reads API key, model, and port from WrenSettings.
     */
    fun start(
        ctx: Context,
        scope: CoroutineScope,
        onReady: () -> Unit,
        onProgress: (String) -> Unit,
        onError: (String) -> Unit = {}
    ) {
        if (running) { onReady(); return }

        serverJob = scope.launch(Dispatchers.IO) {
            try {
                // Read current settings
                currentPort = WrenSettings.getPort(ctx)
                val apiKey = WrenSettings.getApiKey(ctx)
                val model = WrenSettings.getModel(ctx)
                val baseUrl = WrenSettings.getBaseUrl(ctx)

                onProgress("Starting Wren AI...")
                if (!Python.isStarted()) Python.start(AndroidPlatform(ctx))

                val wrenDir = File(ctx.filesDir, "wren")
                val sitePackages = Python.getSitePackagesDir()
                System.setProperty("python.path", "$wrenDir:$sitePackages")

                onProgress("Initializing web server...")
                val py = Python.getInstance()

                // Chaquopy automatically converts Kotlin Maps to Python dicts
                val config = mapOf(
                    "port" to currentPort,
                    "api_key" to apiKey,
                    "model" to model,
                    "base_url" to baseUrl
                )
                py.getModule("wren_server_runner").callAttr("start_server", config)

                // Health-check loop with retry
                onProgress("Waiting for server...")
                var lastError: String? = null
                for (attempt in 1..MAX_RETRIES) {
                    delay(RETRY_DELAY_MS)
                    try {
                        val conn = URL(healthUrl).openConnection() as HttpURLConnection
                        conn.connectTimeout = 2000
                        conn.readTimeout = 2000
                        conn.requestMethod = "GET"
                        val code = conn.responseCode
                        conn.disconnect()
                        if (code == 200) {
                            running = true
                            withContext(Dispatchers.Main) {
                                onProgress("Server ready")
                                onReady()
                            }
                            return@launch
                        }
                        lastError = "HTTP $code"
                    } catch (e: Exception) {
                        lastError = e.message ?: "Connection failed"
                    }
                    withContext(Dispatchers.Main) {
                        onProgress("Connecting... ($attempt/$MAX_RETRIES)")
                    }
                }

                val errorMsg = "Server failed to start after $MAX_RETRIES attempts: $lastError"
                Log.e(TAG, errorMsg)
                running = false
                withContext(Dispatchers.Main) { onError(errorMsg) }
            } catch (e: Exception) {
                Log.e(TAG, "Start failed", e)
                running = false
                withContext(Dispatchers.Main) { onError(e.message ?: "Unknown error") }
            }
        }
    }

    /** Stop the Python server gracefully. */
    fun stop() {
        serverJob?.cancel()
        serverJob = null
        try {
            Python.getInstance().getModule("wren_server_runner").callAttr("stop_server")
        } catch (_: Exception) {}
        running = false
        Log.i(TAG, "Server stopped")
    }

    /** Check if server is currently running. */
    fun isRunning(): Boolean = running

    /** Force-reset state (for crash recovery). */
    fun resetState() {
        running = false
        serverJob = null
    }
}
