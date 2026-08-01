package com.wren.android

import android.content.Context
import android.util.Log
import kotlinx.coroutines.*
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

/**
 * Manages the Wren AI backend server lifecycle.
 *
 * This version connects to an externally-running server (started separately
 * via Docker, CLI, or another device on the network). It does NOT embed
 * Python via Chaquopy — the APK acts as a WebView client.
 */
object ServerManager {
    const val PORT = 12000  // Default port
    private const val MAX_RETRIES = 10
    private const val RETRY_DELAY_MS = 1000L
    private const val TAG = "WrenServer"

    @Volatile
    private var running = false
    private var serverJob: Job? = null

    /** Current port (may differ if user changed it in settings). */
    @Volatile
    var currentPort: Int = PORT
        set

    /** Health check URL derived from current port. */
    private val healthUrl: String get() = "http://127.0.0.1:$currentPort/api/v1/alive"

    /**
     * Start health-check polling.
     *
     * Unlike the Chaquopy version, this does not start a Python process —
     * it simply polls the URL until the backend responds, then signals ready.
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
                currentPort = WrenSettings.getPort(ctx)
                onProgress("Connecting to Wren AI server...")

                var lastError: String? = null
                for (attempt in 1..MAX_RETRIES) {
                    delay(RETRY_DELAY_MS)
                    try {
                        val conn = URL(healthUrl).openConnection() as HttpURLConnection
                        conn.connectTimeout = 3000
                        conn.readTimeout = 2000
                        conn.requestMethod = "GET"
                        val code = conn.responseCode
                        conn.disconnect()
                        if (code in 200..399) {
                            running = true
                            withContext(Dispatchers.Main) {
                                onProgress("Server ready on port $currentPort")
                                onReady()
                            }
                            return@launch
                        }
                        lastError = "HTTP $code"
                    } catch (e: Exception) {
                        lastError = e.message ?: "Connection refused"
                    }
                    withContext(Dispatchers.Main) {
                        onProgress("Connecting... ($attempt/$MAX_RETRIES)")
                    }
                }

                val errorMsg = "Cannot reach Wren AI server at $healthUrl " +
                    "after $MAX_RETRIES attempts. Last error: $lastError\n\n" +
                    "Make sure the server is running. Start it with:\n" +
                    "  docker run -p 12000:12000 wren-ai/server\n" +
                    "or via the Wren CLI:\n" +
                    "  wren serve --port $currentPort"
                Log.e(TAG, errorMsg)
                running = false
                withContext(Dispatchers.Main) { onError(errorMsg) }
            } catch (e: Exception) {
                Log.e(TAG, "Server check failed", e)
                running = false
                withContext(Dispatchers.Main) { onError(e.message ?: "Unknown error") }
            }
        }
    }

    /** Stop the health-check polling. */
    fun stop() {
        serverJob?.cancel()
        serverJob = null
        running = false
        Log.i(TAG, "Server polling stopped")
    }

    /** Check if server connection is active. */
    fun isRunning(): Boolean = running

    /** Force-reset state (for crash recovery). */
    fun resetState() {
        running = false
        serverJob = null
    }
}
