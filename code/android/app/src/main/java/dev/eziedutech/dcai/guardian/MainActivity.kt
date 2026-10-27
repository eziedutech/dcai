package dev.eziedutech.dcai.guardian

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dev.eziedutech.dcai.guardian.data.GuardianStore
import dev.eziedutech.dcai.guardian.net.BackendClient
import dev.eziedutech.dcai.guardian.net.DeviceConfig
import dev.eziedutech.dcai.guardian.service.DeviceState
import dev.eziedutech.dcai.guardian.service.GuardianService
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.launch

private val Navy = Color(0xFF1F3A5F)
private val Ink = Color(0xFF14233A)

class MainActivity : ComponentActivity() {
    private val askNotifications = registerForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.RequestPermission(),
    ) { /* the persistent notification needs this on API 33+; nothing to do with the result */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        if (android.os.Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED
        ) {
            askNotifications.launch(android.Manifest.permission.POST_NOTIFICATIONS)
        }
        val store = ServiceLocator.store(this)
        val paired = MutableStateFlow(store.isPaired)

        setContent {
            MaterialTheme(colorScheme = if (isSystemDark()) darkColorScheme(primary = Color(0xFF9DB4D0)) else lightColorScheme(primary = Navy)) {
                Surface(modifier = Modifier.fillMaxSize()) {
                    val isPaired by paired.collectAsStateWithLifecycle()
                    if (isPaired) {
                        HomeScreen(store, onUnpaired = { paired.value = false })
                    } else {
                        SetupScreen(onPaired = {
                            paired.value = true
                            GuardianService.start(this@MainActivity)
                        })
                    }
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        if (ServiceLocator.store(this).isPaired) GuardianService.start(this)
    }

    @Composable
    private fun isSystemDark(): Boolean =
        resources.configuration.uiMode and android.content.res.Configuration.UI_MODE_NIGHT_MASK == android.content.res.Configuration.UI_MODE_NIGHT_YES
}

@Composable
private fun SetupScreen(onPaired: () -> Unit) {
    val context = androidx.compose.ui.platform.LocalContext.current
    val scope = rememberCoroutineScope()
    var server by remember { mutableStateOf(BuildConfig.DEFAULT_SERVER) }
    var code by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    Column(
        Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(stringResource(R.string.app_name), fontSize = 22.sp, fontWeight = FontWeight.Bold, color = Ink)
        Text(stringResource(R.string.setup_title), fontSize = 26.sp, fontWeight = FontWeight.ExtraBold, color = Ink)
        Text(stringResource(R.string.setup_lead), color = Ink)
        OutlinedTextField(
            value = server, onValueChange = { server = it },
            label = { Text(stringResource(R.string.setup_server)) },
            singleLine = true, modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = code, onValueChange = { code = it.uppercase() },
            label = { Text(stringResource(R.string.setup_code)) },
            singleLine = true, modifier = Modifier.fillMaxWidth(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Ascii),
        )
        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        Button(
            onClick = {
                error = null
                busy = true
                scope.launch {
                    val result = pair(context.applicationContext as android.content.Context, server.trim(), code.trim())
                    busy = false
                    result.fold(onSuccess = { onPaired() }, onFailure = { error = it.message })
                }
            },
            enabled = !busy && code.isNotBlank() && server.isNotBlank(),
            modifier = Modifier.fillMaxWidth(),
        ) {
            if (busy) CircularProgressIndicator(Modifier.padding(end = 8.dp), strokeWidth = 2.dp)
            Text(stringResource(if (busy) R.string.setup_pairing else R.string.setup_pair))
        }
    }
}

private suspend fun pair(context: android.content.Context, server: String, code: String): Result<Unit> {
    val store = GuardianStore(context)
    val client = BackendClient(server) { null }
    return runCatching {
        val response = client.pair(code, deviceName = android.os.Build.MODEL ?: "Android", appVersion = BuildConfig.VERSION_NAME)
        store.serverUrl = server
        store.deviceToken = response.deviceToken
        store.config = response.config
        ServiceLocator.reset()
    }.recoverCatching { e ->
        throw IllegalStateException(
            when (e) {
                is dev.eziedutech.dcai.guardian.net.BackendException -> context.getString(R.string.setup_error)
                else -> context.getString(R.string.setup_neterror)
            },
        )
    }
}

@Composable
private fun HomeScreen(store: GuardianStore, onUnpaired: () -> Unit) {
    val context = androidx.compose.ui.platform.LocalContext.current
    val config = store.config
    if (config == null) {
        onUnpaired()
        return
    }
    val keyboardOn = remember { mutableStateOf(DeviceState.isKeyboardEnabled(context)) }

    Column(
        Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(
            if (config.childNickname.isNotBlank()) stringResource(R.string.home_active_for, config.childNickname) else stringResource(R.string.home_active),
            fontSize = 24.sp, fontWeight = FontWeight.ExtraBold, color = Ink,
        )
        Text(stringResource(R.string.home_transparency), color = Ink)

        SectionCard(stringResource(R.string.home_what_title)) {
            Text(stringResource(R.string.how_1), color = Ink)
            Text(stringResource(R.string.how_2), color = Ink)
            Text(stringResource(R.string.how_3), color = Ink)
        }

        SectionCard(stringResource(R.string.home_scopes_title)) {
            config.scopes.forEach { scope ->
                Text("•  " + scopeLabel(scope), color = Ink)
            }
        }

        SectionCard(stringResource(R.string.home_keyboard_title)) {
            Text(
                if (keyboardOn.value) stringResource(R.string.home_keyboard_on) else stringResource(R.string.home_keyboard_off),
                color = Ink,
            )
            OutlinedButton(onClick = {
                context.startActivity(Intent(Settings.ACTION_INPUT_METHOD_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            }) { Text(stringResource(R.string.home_keyboard_enable)) }
        }
    }
}

@Composable
private fun SectionCard(title: String, content: @Composable () -> Unit) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(title, fontWeight = FontWeight.Bold, color = Ink)
            content()
        }
    }
}

@Composable
private fun scopeLabel(scope: String): String = stringResource(
    when (scope) {
        "percakapan" -> R.string.scope_percakapan
        "gambar" -> R.string.scope_gambar
        "domain" -> R.string.scope_domain
        "suara" -> R.string.scope_suara
        "keyboard" -> R.string.scope_keyboard
        else -> R.string.scope_percakapan
    },
)

@Composable
private fun stringResource(id: Int, vararg args: Any): String =
    androidx.compose.ui.platform.LocalContext.current.getString(id, *args)
