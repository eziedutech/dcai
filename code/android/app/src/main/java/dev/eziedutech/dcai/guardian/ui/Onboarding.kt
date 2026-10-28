package dev.eziedutech.dcai.guardian.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Info
import androidx.compose.material.icons.rounded.Language
import androidx.compose.material.icons.rounded.Notifications
import androidx.compose.material.icons.rounded.Translate
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import dev.eziedutech.dcai.guardian.BuildConfig
import dev.eziedutech.dcai.guardian.R
import dev.eziedutech.dcai.guardian.net.DeviceConfig
import dev.eziedutech.dcai.guardian.privacy.Pin
import dev.eziedutech.dcai.guardian.ui.art.Art
import dev.eziedutech.dcai.guardian.ui.art.Illustration
import dev.eziedutech.dcai.guardian.ui.theme.BrandBlue
import dev.eziedutech.dcai.guardian.ui.theme.BrandLeaf
import kotlinx.coroutines.launch

private const val SETUP_STEPS = 4

@Composable
private fun OnboardingScaffold(step: Int?, onBack: (() -> Unit)?, content: @Composable ColumnScope.() -> Unit, bottom: @Composable ColumnScope.() -> Unit) {
    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).safeDrawingPadding()) {
        Row(Modifier.fillMaxWidth().height(56.dp).padding(horizontal = 12.dp), verticalAlignment = Alignment.CenterVertically) {
            if (onBack != null) TextButton(onClick = onBack) { Text(stringResource(R.string.action_back)) } else Spacer(Modifier.width(8.dp))
            Spacer(Modifier.weight(1f))
            if (step != null) {
                Text(stringResource(R.string.step_of, step, SETUP_STEPS), style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Spacer(Modifier.width(12.dp))
        }
        if (step != null) {
            LinearProgressIndicator(
                progress = { step / SETUP_STEPS.toFloat() },
                modifier = Modifier.fillMaxWidth().padding(horizontal = 24.dp).height(6.dp).clip(RoundedCornerShape(3.dp)),
            )
        }
        Column(
            Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(horizontal = 24.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) { content() }
        Column(Modifier.padding(horizontal = 24.dp, vertical = 16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) { bottom() }
    }
}

@Composable
fun WelcomeScreen(onLanguage: () -> Unit, onStart: () -> Unit) {
    Box(
        Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(BrandBlue, Color(0xFF2B63D1), BrandLeaf))).safeDrawingPadding(),
    ) {
        Box(
            Modifier.align(Alignment.TopEnd).padding(16.dp).size(44.dp).clip(CircleShape)
                .background(Color.White.copy(alpha = 0.18f)).clickable(onClick = onLanguage),
            contentAlignment = Alignment.Center,
        ) {
            Icon(Icons.Rounded.Translate, stringResource(R.string.set_language), tint = Color.White, modifier = Modifier.size(22.dp))
        }
        // Light status bar icons on the blue background; restored when the screen leaves.
        val view = androidx.compose.ui.platform.LocalView.current
        val darkTheme = androidx.compose.foundation.isSystemInDarkTheme()
        androidx.compose.runtime.DisposableEffect(Unit) {
            val window = (view.context as? android.app.Activity)?.window
            val controller = window?.let { androidx.core.view.WindowCompat.getInsetsController(it, view) }
            controller?.isAppearanceLightStatusBars = false
            onDispose { controller?.isAppearanceLightStatusBars = !darkTheme }
        }
        Column(
            Modifier.fillMaxSize().padding(horizontal = 28.dp, vertical = 24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            LogoBadge(132.dp)
            Spacer(Modifier.height(28.dp))
            Text(stringResource(R.string.brand_title), style = MaterialTheme.typography.headlineMedium, color = Color.White, textAlign = TextAlign.Center)
            Text(stringResource(R.string.brand_subtitle), style = MaterialTheme.typography.titleLarge, color = Color.White.copy(alpha = 0.95f), textAlign = TextAlign.Center)
            Spacer(Modifier.height(16.dp))
            Text(stringResource(R.string.welcome_tagline), style = MaterialTheme.typography.titleMedium, color = Color.White.copy(alpha = 0.92f), textAlign = TextAlign.Center)
            Spacer(Modifier.height(48.dp))
        }
        Column(Modifier.align(Alignment.BottomCenter).padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            androidx.compose.material3.Button(
                onClick = onStart, modifier = Modifier.fillMaxWidth().height(56.dp), shape = RoundedCornerShape(18.dp),
                colors = androidx.compose.material3.ButtonDefaults.buttonColors(containerColor = Color.White, contentColor = BrandBlue),
            ) { Text(stringResource(R.string.welcome_start), style = MaterialTheme.typography.labelLarge) }
            Spacer(Modifier.height(12.dp))
            Text(stringResource(R.string.welcome_note), color = Color.White.copy(alpha = 0.85f), style = MaterialTheme.typography.bodySmall, textAlign = TextAlign.Center)
        }
    }
}

private data class Slide(val art: Art, val title: Int, val body: Int)

@Composable
fun IntroScreen(onDone: () -> Unit) {
    val slides = listOf(
        Slide(Art.CHAT, R.string.intro1_title, R.string.intro1_body),
        Slide(Art.SHIELD, R.string.intro2_title, R.string.intro2_body),
        Slide(Art.FAMILY, R.string.intro3_title, R.string.intro3_body),
    )
    val pager = rememberPagerState { slides.size }
    val scope = rememberCoroutineScope()
    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).safeDrawingPadding()) {
        Row(Modifier.fillMaxWidth().padding(8.dp)) {
            Spacer(Modifier.weight(1f))
            TextButton(onClick = onDone) { Text(stringResource(R.string.action_skip)) }
        }
        HorizontalPager(pager, Modifier.weight(1f)) { page ->
            val s = slides[page]
            Column(Modifier.fillMaxSize().padding(horizontal = 32.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
                Illustration(s.art, Modifier.fillMaxWidth(0.82f))
                Spacer(Modifier.height(28.dp))
                Text(stringResource(s.title), style = MaterialTheme.typography.headlineMedium, textAlign = TextAlign.Center)
                Spacer(Modifier.height(12.dp))
                CenteredText(stringResource(s.body))
            }
        }
        Row(Modifier.fillMaxWidth().padding(vertical = 12.dp), horizontalArrangement = Arrangement.Center) {
            repeat(slides.size) { i ->
                Box(
                    Modifier.padding(4.dp).height(8.dp).width(if (i == pager.currentPage) 24.dp else 8.dp).clip(CircleShape)
                        .background(if (i == pager.currentPage) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outlineVariant),
                )
            }
        }
        Box(Modifier.padding(24.dp)) {
            val last = pager.currentPage == slides.lastIndex
            PrimaryButton(stringResource(if (last) R.string.action_continue else R.string.action_next), onClick = {
                if (last) onDone() else scope.launch { pager.animateScrollToPage(pager.currentPage + 1) }
            })
        }
    }
}

@Composable
fun ConnectScreen(onBack: () -> Unit, pair: suspend (server: String, code: String) -> String?, onPaired: () -> Unit) {
    val scope = rememberCoroutineScope()
    var server by remember { mutableStateOf(BuildConfig.DEFAULT_SERVER) }
    var code by remember { mutableStateOf("") }
    var advanced by remember { mutableStateOf(false) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    OnboardingScaffold(step = 1, onBack = onBack, content = {
        Illustration(Art.FAMILY, Modifier.fillMaxWidth(0.55f).align(Alignment.CenterHorizontally))
        Text(stringResource(R.string.connect_title), style = MaterialTheme.typography.headlineMedium)
        Text(stringResource(R.string.connect_lead), color = MaterialTheme.colorScheme.onSurfaceVariant)
        OutlinedTextField(
            value = code, onValueChange = { code = it.uppercase().take(12) },
            label = { Text(stringResource(R.string.setup_code)) }, placeholder = { Text("ABCD-EFGH") },
            singleLine = true, modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(14.dp),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Ascii),
        )
        TextButton(onClick = { advanced = !advanced }) { Text(stringResource(R.string.connect_advanced)) }
        AnimatedVisibility(advanced) {
            OutlinedTextField(
                value = server, onValueChange = { server = it }, label = { Text(stringResource(R.string.setup_server)) },
                singleLine = true, modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(14.dp),
            )
        }
        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
    }, bottom = {
        PrimaryButton(
            stringResource(if (busy) R.string.setup_pairing else R.string.setup_pair),
            enabled = !busy && code.length >= 8 && server.isNotBlank(),
            onClick = {
                busy = true
                error = null
                scope.launch {
                    error = pair(server.trim(), code.trim())
                    busy = false
                    if (error == null) onPaired()
                }
            },
        )
        if (busy) CircularProgressIndicator(Modifier.align(Alignment.CenterHorizontally).size(24.dp), strokeWidth = 2.dp)
    })
}

@Composable
fun ConsentScreen(config: DeviceConfig, onReadFull: () -> Unit, onAccepted: () -> Unit) {
    var guardian by remember { mutableStateOf(false) }
    var together by remember { mutableStateOf(false) }
    OnboardingScaffold(step = 2, onBack = null, content = {
        Illustration(Art.CONSENT, Modifier.fillMaxWidth(0.5f).align(Alignment.CenterHorizontally))
        Text(stringResource(R.string.consent_title), style = MaterialTheme.typography.headlineMedium)
        Text(stringResource(R.string.consent_lead, config.childNickname), color = MaterialTheme.colorScheme.onSurfaceVariant)
        GroupCard {
            Feature.entries.filter { config.has(it.scope) }.forEach { f ->
                SettingRow(f.icon, stringResource(f.title), stringResource(f.short), trailing = null)
            }
        }
        TextButton(onClick = onReadFull) { Text(stringResource(R.string.consent_read_full)) }
        CheckRow(guardian, { guardian = it }, stringResource(R.string.consent_check_guardian))
        CheckRow(together, { together = it }, stringResource(R.string.consent_check_together))
    }, bottom = {
        PrimaryButton(stringResource(R.string.consent_accept), onClick = onAccepted, enabled = guardian && together)
    })
}

@Composable
private fun CheckRow(checked: Boolean, onChange: (Boolean) -> Unit, text: String) {
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).background(MaterialTheme.colorScheme.surface)
            .clickable { onChange(!checked) }.padding(12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Checkbox(checked, onChange)
        Spacer(Modifier.width(8.dp))
        Text(text, style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
fun PinSetupScreen(onBack: (() -> Unit)?, onSaved: (String) -> Unit, step: Int? = 3) {
    var pin by remember { mutableStateOf("") }
    var again by remember { mutableStateOf("") }
    val mismatch = again.length >= 4 && again != pin
    OnboardingScaffold(step = step, onBack = onBack, content = {
        Illustration(Art.PIN, Modifier.fillMaxWidth(0.5f).align(Alignment.CenterHorizontally))
        Text(stringResource(R.string.pin_title), style = MaterialTheme.typography.headlineMedium)
        Text(stringResource(R.string.pin_lead), color = MaterialTheme.colorScheme.onSurfaceVariant)
        PinField(pin, { pin = it }, stringResource(R.string.setup_pin))
        PinField(again, { again = it }, stringResource(R.string.pin_again))
        if (mismatch) Text(stringResource(R.string.pin_mismatch), color = MaterialTheme.colorScheme.error)
    }, bottom = {
        PrimaryButton(stringResource(R.string.pin_save), onClick = { onSaved(pin) }, enabled = Pin.valid(pin) && pin == again)
    })
}

@Composable
fun PermissionsScreen(
    snapshot: Snapshot,
    onNotifications: () -> Unit,
    onSites: () -> Unit,
    onKeyboard: () -> Unit,
    onDone: () -> Unit,
) {
    OnboardingScaffold(step = 4, onBack = null, content = {
        Text(stringResource(R.string.perm_title), style = MaterialTheme.typography.headlineMedium)
        Text(stringResource(R.string.perm_lead), color = MaterialTheme.colorScheme.onSurfaceVariant)
        GroupCard {
            SwitchRow(
                Icons.Rounded.Notifications, stringResource(R.string.perm_notifications), stringResource(R.string.perm_notifications_sub),
                if (snapshot.notificationsOn) Status.ON else Status.NEEDS_SETUP, snapshot.notificationsOn,
            ) { if (!snapshot.notificationsOn) onNotifications() }
            if (snapshot.granted(Feature.SITUS)) {
                SwitchRow(
                    Icons.Rounded.Language, stringResource(R.string.f_site), stringResource(R.string.f_site_short),
                    snapshot.status(Feature.SITUS), snapshot.sitesOn,
                ) { if (!snapshot.sitesOn) onSites() }
            }
            if (snapshot.granted(Feature.PAPAN_KETIK)) {
                SwitchRow(
                    Feature.PAPAN_KETIK.icon, stringResource(R.string.f_keyboard), stringResource(R.string.f_keyboard_short),
                    snapshot.status(Feature.PAPAN_KETIK), snapshot.keyboardOn,
                ) { onKeyboard() }
            }
        }
        Row(
            Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(MaterialTheme.colorScheme.secondaryContainer).padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(Icons.Rounded.Info, null, tint = BrandLeaf)
            Spacer(Modifier.width(12.dp))
            Text(stringResource(R.string.perm_note), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSecondaryContainer)
        }
    }, bottom = {
        PrimaryButton(stringResource(R.string.perm_done), onClick = onDone, enabled = snapshot.notificationsOn)
        if (!snapshot.notificationsOn) {
            Text(stringResource(R.string.perm_required), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Medium)
        }
    })
}
