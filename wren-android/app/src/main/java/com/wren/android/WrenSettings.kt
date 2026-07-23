package com.wren.android

import android.content.Context

/**
 * Centralized access to all app settings stored in SharedPreferences.
 * Used by ServerManager, WrenService, and SettingsActivity.
 */
object WrenSettings {
    private const val PREFS_NAME = "wren_settings"

    // Keys
    private const val KEY_API_KEY = "llm_api_key"
    private const val KEY_MODEL = "llm_model"
    private const val KEY_PORT = "server_port"
    private const val KEY_AUTO_START = "auto_start"
    private const val KEY_BASE_URL = "llm_base_url"

    // Defaults
    const val DEFAULT_PORT = 12000
    const val DEFAULT_MODEL = "wren/o3"
    const val DEFAULT_BASE_URL = ""

    private fun prefs(ctx: Context) =
        ctx.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    /** LLM API key (sk-... or wren_...) */
    fun getApiKey(ctx: Context): String =
        prefs(ctx).getString(KEY_API_KEY, "") ?: ""

    fun setApiKey(ctx: Context, value: String) {
        prefs(ctx).edit().putString(KEY_API_KEY, value).apply()
    }

    /** LLM model identifier (e.g. "wren/o3", "openai/gpt-4o") */
    fun getModel(ctx: Context): String =
        prefs(ctx).getString(KEY_MODEL, DEFAULT_MODEL) ?: DEFAULT_MODEL

    fun setModel(ctx: Context, value: String) {
        prefs(ctx).edit().putString(KEY_MODEL, value).apply()
    }

    /** Server port for the Python backend */
    fun getPort(ctx: Context): Int =
        prefs(ctx).getInt(KEY_PORT, DEFAULT_PORT)

    fun setPort(ctx: Context, value: Int) {
        prefs(ctx).edit().putInt(KEY_PORT, value).apply()
    }

    /** Whether to auto-start server on phone boot */
    fun isAutoStart(ctx: Context): Boolean =
        prefs(ctx).getBoolean(KEY_AUTO_START, true)

    fun setAutoStart(ctx: Context, value: Boolean) {
        prefs(ctx).edit().putBoolean(KEY_AUTO_START, value).apply()
    }

    /** Optional custom base URL for LLM API (empty = use provider default) */
    fun getBaseUrl(ctx: Context): String =
        prefs(ctx).getString(KEY_BASE_URL, DEFAULT_BASE_URL) ?: DEFAULT_BASE_URL

    fun setBaseUrl(ctx: Context, value: String) {
        prefs(ctx).edit().putString(KEY_BASE_URL, value).apply()
    }
}
