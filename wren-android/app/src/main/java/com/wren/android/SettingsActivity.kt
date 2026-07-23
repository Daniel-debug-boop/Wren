package com.wren.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob

class SettingsActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(colorScheme = darkColorScheme()) {
                SettingsScreen(onBack = { finish() })
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SettingsScreen(onBack: () -> Unit) {
    val context = LocalContext.current

    var apiKey by remember { mutableStateOf(WrenSettings.getApiKey(context)) }
    var selectedModel by remember { mutableStateOf(WrenSettings.getModel(context)) }
    var serverPort by remember { mutableStateOf(WrenSettings.getPort(context).toString()) }
    var autoStart by remember { mutableStateOf(WrenSettings.isAutoStart(context)) }
    var baseUrl by remember { mutableStateOf(WrenSettings.getBaseUrl(context)) }
    var showApiKey by remember { mutableStateOf(false) }
    var showBaseUrl by remember { mutableStateOf(false) }
    var modelDropdownExpanded by remember { mutableStateOf(false) }
    var saved by remember { mutableStateOf(false) }

    val models = listOf(
        "wren/o3" to "Wren O3 (Recommended)",
        "wren/gpt-4o" to "GPT-4o via Wren",
        "wren/claude-sonnet-4-20250514" to "Claude Sonnet via Wren",
        "wren/gemini-2.0-flash" to "Gemini Flash via Wren",
        "openai/gpt-4o" to "GPT-4o (Direct)",
        "anthropic/claude-sonnet-4-20250514" to "Claude Sonnet (Direct)"
    )

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings", fontWeight = FontWeight.SemiBold) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF0A0A0F),
                    titleContentColor = Color.White,
                    navigationIconContentColor = Color.White
                )
            )
        },
        containerColor = Color(0xFF0A0A0F)
    ) { padding ->
        Column(
            Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp)
        ) {
            // ── LLM Configuration ────────────────────────────────────
            SectionHeader("LLM Configuration")

            SettingsCard {
                // API Key
                SettingsRow(
                    icon = Icons.Default.Key,
                    title = "API Key",
                    subtitle = if (apiKey.isNotBlank()) "•••••••${apiKey.takeLast(4)}" else "Not set"
                ) {
                    OutlinedTextField(
                        value = apiKey,
                        onValueChange = { apiKey = it; saved = false },
                        modifier = Modifier.fillMaxWidth(),
                        placeholder = { Text("sk-... or wren_...", color = Color(0xFF666677)) },
                        visualTransformation = if (showApiKey) VisualTransformation.None
                            else PasswordVisualTransformation(),
                        trailingIcon = {
                            IconButton(onClick = { showApiKey = !showApiKey }) {
                                Icon(
                                    if (showApiKey) Icons.Default.VisibilityOff else Icons.Default.Visibility,
                                    "Toggle visibility",
                                    tint = Color(0xFF888899)
                                )
                            }
                        },
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = Color(0xFFC9B974),
                            unfocusedBorderColor = Color(0xFF2A2A35),
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        ),
                        singleLine = true
                    )
                }

                HorizontalDivider(color = Color(0xFF1A1A2E))

                // Base URL (for custom LLM endpoints)
                SettingsRow(
                    icon = Icons.Default.Language,
                    title = "Base URL",
                    subtitle = if (baseUrl.isNotBlank()) baseUrl else "Provider default"
                ) {
                    OutlinedTextField(
                        value = baseUrl,
                        onValueChange = { baseUrl = it; saved = false },
                        modifier = Modifier.fillMaxWidth(),
                        placeholder = { Text("https://api.openai.com/v1", color = Color(0xFF666677)) },
                        visualTransformation = if (showBaseUrl) VisualTransformation.None
                            else PasswordVisualTransformation(),
                        trailingIcon = {
                            IconButton(onClick = { showBaseUrl = !showBaseUrl }) {
                                Icon(
                                    if (showBaseUrl) Icons.Default.VisibilityOff else Icons.Default.Visibility,
                                    "Toggle visibility",
                                    tint = Color(0xFF888899)
                                )
                            }
                        },
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = Color(0xFFC9B974),
                            unfocusedBorderColor = Color(0xFF2A2A35),
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        ),
                        singleLine = true
                    )
                }

                HorizontalDivider(color = Color(0xFF1A1A2E))

                // Model Selection
                SettingsRow(
                    icon = Icons.Default.SmartToy,
                    title = "Model",
                    subtitle = models.find { it.first == selectedModel }?.second ?: selectedModel
                ) {
                    ExposedDropdownMenuBox(
                        expanded = modelDropdownExpanded,
                        onExpandedChange = { modelDropdownExpanded = it }
                    ) {
                        OutlinedTextField(
                            value = models.find { it.first == selectedModel }?.second ?: selectedModel,
                            onValueChange = {},
                            readOnly = true,
                            modifier = Modifier.fillMaxWidth().menuAnchor(),
                            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(modelDropdownExpanded) },
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = Color(0xFFC9B974),
                                unfocusedBorderColor = Color(0xFF2A2A35),
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White
                            )
                        )
                        ExposedDropdownMenu(
                            expanded = modelDropdownExpanded,
                            onDismissRequest = { modelDropdownExpanded = false }
                        ) {
                            models.forEach { (id, name) ->
                                DropdownMenuItem(
                                    text = { Text(name, color = Color.White) },
                                    onClick = { selectedModel = id; modelDropdownExpanded = false; saved = false },
                                    containerColor = if (id == selectedModel) Color(0xFF1A1A2E) else Color(0xFF0A0A0F)
                                )
                            }
                        }
                    }
                }
            }

            Spacer(Modifier.height(24.dp))

            // ── Server Configuration ──────────────────────────────────
            SectionHeader("Server")

            SettingsCard {
                SettingsRow(
                    icon = Icons.Default.Settings,
                    title = "Server Port",
                    subtitle = "Default: ${WrenSettings.DEFAULT_PORT}"
                ) {
                    OutlinedTextField(
                        value = serverPort,
                        onValueChange = { serverPort = it; saved = false },
                        modifier = Modifier.width(100.dp),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = Color(0xFFC9B974),
                            unfocusedBorderColor = Color(0xFF2A2A35),
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        ),
                        singleLine = true
                    )
                }

                HorizontalDivider(color = Color(0xFF1A1A2E))

                SettingsRow(
                    icon = Icons.Default.PlayArrow,
                    title = "Auto-start on boot",
                    subtitle = "Start server when phone boots"
                ) {
                    Switch(
                        checked = autoStart,
                        onCheckedChange = { autoStart = it; saved = false },
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = Color(0xFFC9B974),
                            checkedTrackColor = Color(0xFFC9B974).copy(alpha = 0.3f),
                            uncheckedThumbColor = Color(0xFF666677),
                            uncheckedTrackColor = Color(0xFF1A1A2E)
                        )
                    )
                }
            }

            Spacer(Modifier.height(24.dp))

            // ── About ─────────────────────────────────────────────────
            SectionHeader("About")

            SettingsCard {
                SettingsRow(
                    icon = Icons.Default.Info,
                    title = "Wren AI",
                    subtitle = "Version 1.0.0"
                ) {}

                HorizontalDivider(color = Color(0xFF1A1A2E))

                SettingsRow(
                    icon = Icons.Default.Code,
                    title = "Build",
                    subtitle = "ARM64 • Chaquopy • Compose"
                ) {}
            }

            Spacer(Modifier.height(32.dp))

            // ── Save Button ───────────────────────────────────────────
            Button(
                onClick = {
                    val newPort = serverPort.toIntOrNull() ?: WrenSettings.DEFAULT_PORT
                    WrenSettings.setApiKey(context, apiKey)
                    WrenSettings.setModel(context, selectedModel)
                    WrenSettings.setPort(context, newPort)
                    WrenSettings.setAutoStart(context, autoStart)
                    WrenSettings.setBaseUrl(context, baseUrl)

                    // Propagate to ServerManager so the backend actually uses these values
                    ServerManager.currentPort = newPort

                    // If server is running, restart it with new settings
                    if (ServerManager.isRunning()) {
                        ServerManager.stop()
                        // Brief delay to release port then restart with new config
                        android.os.Handler(mainLooper).postDelayed({
                            val restartScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
                            ServerManager.start(
                                ctx = context,
                                scope = restartScope,
                                onReady = { /* server restarted */ },
                                onProgress = {},
                                onError = {}
                            )
                        }, 500)
                    }

                    saved = true
                },
                modifier = Modifier.fillMaxWidth().height(48.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFC9B974)),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text(
                    if (saved) "✓ Saved" else "Save Settings",
                    color = Color(0xFF0A0A0F),
                    fontWeight = FontWeight.SemiBold
                )
            }

            Spacer(Modifier.height(48.dp))
        }
    }
}

// ── Reusable composables ───────────────────────────────────────────────────

@Composable
private fun SectionHeader(title: String) {
    Text(
        title.uppercase(),
        fontSize = 11.sp,
        fontWeight = FontWeight.SemiBold,
        color = Color(0xFF666677),
        letterSpacing = 1.5.sp,
        modifier = Modifier.padding(bottom = 8.dp)
    )
}

@Composable
private fun SettingsCard(content: @Composable ColumnScope.() -> Unit) {
    Surface(
        color = Color(0xFF12121A),
        shape = RoundedCornerShape(12.dp),
        tonalElevation = 2.dp
    ) {
        Column(Modifier.padding(4.dp), content = content)
    }
}

@Composable
private fun SettingsRow(
    icon: ImageVector,
    title: String,
    subtitle: String,
    trailing: @Composable () -> Unit
) {
    Row(
        Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(icon, null, tint = Color(0xFFC9B974), modifier = Modifier.size(20.dp))
        Spacer(Modifier.width(16.dp))
        Column(Modifier.weight(1f)) {
            Text(title, color = Color.White, fontSize = 15.sp, fontWeight = FontWeight.Medium)
            Text(subtitle, color = Color(0xFF666677), fontSize = 12.sp)
        }
        trailing()
    }
}
