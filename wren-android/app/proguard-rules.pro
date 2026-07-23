# ── Wren Android ProGuard Rules ─────────────────────────────────────────────

# Keep all Wren app classes (needed for Chaquopy reflection)
-keep class com.wren.android.** { *; }
-keepclassmembers class com.wren.android.** { *; }

# ── Chaquopy (Python on Android) ────────────────────────────────────────────
-keep class com.chaquo.python.** { *; }
-dontwarn com.chaquo.python.**
-keepclassmembers class com.chaquo.python.** { *; }

# Keep Python module names referenced via Chaquopy
-keep class com.chaquo.python.Python { *; }
-keep class com.chaquo.python.android.AndroidPlatform { *; }

# ── Compose ─────────────────────────────────────────────────────────────────
-dontwarn androidx.compose.**
-keep class androidx.compose.** { *; }

# ── Kotlin Coroutines ───────────────────────────────────────────────────────
-keepnames class kotlinx.coroutines.internal.MainDispatcherFactory {}
-keepnames class kotlinx.coroutines.CoroutineExceptionHandler {}
-keepclassmembers class kotlinx.coroutines.** {
    volatile <fields>;
}

# ── FastAPI / Uvicorn (bundled Python) ──────────────────────────────────────
-dontwarn fastapi.**
-dontwarn uvicorn.**
-dontwarn starlette.**
-dontwarn pydantic.**

# ── General Android ─────────────────────────────────────────────────────────
-keepattributes *Annotation*
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile

# Keep JavaScript interface methods (used by WebView)
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# Remove verbose/debug logging in release (keep info and above)
-assumenosideeffects class android.util.Log {
    public static int v(...);
    public static int d(...);
}
