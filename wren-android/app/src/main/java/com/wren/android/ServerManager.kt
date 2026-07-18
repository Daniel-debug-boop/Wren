package com.wren.android

import android.content.Context
import android.util.Log
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.io.File

object ServerManager {
    const val PORT = 12000

    private var running = false

    fun start(ctx: Context, onReady: () -> Unit, onProgress: (String) -> Unit) {
        if (running) { onReady(); return }

        try {
            onProgress("Starting Wren AI...")
            if (!Python.isStarted()) Python.start(AndroidPlatform(ctx))

            val wrenDir = File(ctx.filesDir, "wren")
            val sitePackages = Python.getSitePackagesDir()
            System.setProperty("python.path", "$wrenDir:$sitePackages")

            onProgress("Initializing web server...")
            val py = Python.getInstance()
            py.getModule("wren_server_runner").callAttr("start_server", PORT)

            running = true
            onProgress("Server ready on port $PORT")
            onReady()
        } catch (e: Exception) {
            Log.e("WrenServer", "Start failed", e)
            onProgress("Error: ${e.message}")
            running = false
        }
    }

    fun stop() {
        try {
            Python.getInstance().getModule("wren_server_runner").callAttr("stop_server")
        } catch (_: Exception) {}
        running = false
    }
}
