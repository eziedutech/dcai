package dev.eziedutech.dcai.guardian

import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import dev.eziedutech.dcai.guardian.data.GuardianStore
import dev.eziedutech.dcai.guardian.net.BackendClient
import dev.eziedutech.dcai.guardian.net.BackendException
import dev.eziedutech.dcai.guardian.service.GuardianService
import dev.eziedutech.dcai.guardian.sites.SiteGuardVpn
import dev.eziedutech.dcai.guardian.ui.AppLocale
import dev.eziedutech.dcai.guardian.ui.ChoiceDialog
import dev.eziedutech.dcai.guardian.ui.ConnectScreen
import dev.eziedutech.dcai.guardian.ui.ConsentScreen
import dev.eziedutech.dcai.guardian.ui.DeviceInfo
import dev.eziedutech.dcai.guardian.ui.Feature
import dev.eziedutech.dcai.guardian.ui.FeatureDetailScreen
import dev.eziedutech.dcai.guardian.ui.HomeTab
import dev.eziedutech.dcai.guardian.ui.IntroScreen
import dev.eziedutech.dcai.guardian.ui.LocalizedActivity
import dev.eziedutech.dcai.guardian.ui.AboutScreen
import dev.eziedutech.dcai.guardian.ui.MainBottomBar
import dev.eziedutech.dcai.guardian.ui.PermissionsScreen
import dev.eziedutech.dcai.guardian.ui.PinDialog
import dev.eziedutech.dcai.guardian.ui.PinSetupScreen
import dev.eziedutech.dcai.guardian.ui.ProtectionTab
import dev.eziedutech.dcai.guardian.ui.SettingsTab
import dev.eziedutech.dcai.guardian.ui.Snapshot
import dev.eziedutech.dcai.guardian.ui.Tab
import dev.eziedutech.dcai.guardian.ui.TextPage
import dev.eziedutech.dcai.guardian.ui.UiPrefs
import dev.eziedutech.dcai.guardian.ui.WelcomeScreen
import dev.eziedutech.dcai.guardian.ui.art.Art
import dev.eziedutech.dcai.guardian.ui.theme.DcaiTheme
import kotlinx.coroutines.delay

/** Where the app is. Onboarding comes first; the main app has three tabs. */
private sealed interface Route {
    data object Welcome : Route
    data object Intro : Route
    data object Connect : Route
    data object Consent : Route
    data object PinSetup : Route
    data object ChangePin : Route
    data object Permissions : Route
    data object Main : Route
    data class Detail(val feature: Feature) : Route
    data object Transparency : Route
    data object ConsentText : Route
    data object Licenses : Route
    data object About : Route
}

class MainActivity : LocalizedActivity() {
    /** Bumped on every resume, so indicators show what is true now. */
    private val resumeTick = mutableIntStateOf(0)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            var theme by remember { mutableStateOf(UiPrefs(this).theme) }
            DcaiTheme(theme) {
                Surface(Modifier.fillMaxSize()) {
                    App(resumeTick.intValue, theme, onTheme = { UiPrefs(this).theme = it; theme = it })
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        resumeTick.intValue++
        val store = ServiceLocator.store(this)
        if (store.isPaired && store.setupDone) GuardianService.start(this)
    }

    private fun startRoute(store: GuardianStore): Route = when {
        !store.isPaired -> Route.Welcome
        store.consentRead == null -> Route.Consent
        !store.hasPin -> Route.PinSetup
        !store.setupDone -> Route.Permissions
        else -> Route.Main
    }

    @Composable
    private fun App(tick: Int, theme: String, onTheme: (String) -> Unit) {
        val context = LocalContext.current
        val store = remember { ServiceLocator.store(context) }
        val stack = remember { mutableStateListOf(startRoute(store)) }
        var refresh by remember { mutableIntStateOf(0) }
        var settle by remember { mutableIntStateOf(0) }
        val snapshot = remember(tick, refresh, settle) { Snapshot.read(context) }
        var tab by remember { mutableStateOf(Tab.HOME) }
        var dialog by remember { mutableStateOf<String?>(null) }
        var pinPurpose by remember { mutableStateOf<String?>(null) }
        var consentText by remember { mutableStateOf<List<String>?>(null) }

        fun go(route: Route) = stack.add(route)
        fun replaceAll(route: Route) { stack.clear(); stack.add(route) }
        fun back() { if (stack.size > 1) stack.removeAt(stack.lastIndex) else finish() }

        // Services start and stop on their own (the VPN after a restart, a permission changed
        // in settings); read the state again every few seconds while the app is open.
        LaunchedEffect(Unit) {
            while (true) {
                delay(3000)
                settle++
            }
        }
        LaunchedEffect(refresh) {
            // The VPN's state settles a moment after starting or stopping it.
            if (refresh > 0) {
                delay(800)
                settle++
            }
        }

        val askNotifications = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { refresh++ }
        val askVpn = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
            if (result.resultCode == RESULT_OK) {
                store.sitesEnabled = true
                SiteGuardVpn.start(context)
            }
            refresh++
        }

        fun notifications() {
            if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                askNotifications.launch(android.Manifest.permission.POST_NOTIFICATIONS)
            } else {
                startActivity(Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, packageName))
            }
        }

        fun sitesOn() {
            val prepare = VpnService.prepare(context)
            if (prepare != null) askVpn.launch(prepare) else {
                store.sitesEnabled = true
                SiteGuardVpn.start(context)
                refresh++
            }
        }

        fun keyboardSettings() = startActivity(Intent(Settings.ACTION_INPUT_METHOD_SETTINGS))

        fun usageSettings() = startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))

        fun messagesSettings() = startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))

        fun accessibilitySettings() = startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))

        fun overlaySettings() = startActivity(
            Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, android.net.Uri.parse("package:$packageName")),
        )

        fun askTime() = startActivity(Intent(context, dev.eziedutech.dcai.guardian.screen.TimeOutActivity::class.java))

        val languageLabel = languageName(AppLocale.current(context))
        val route = stack.last()
        BackHandler(enabled = stack.size > 1) { back() }

        AnimatedContent(route, transitionSpec = { fadeIn() togetherWith fadeOut() }, label = "route") { r ->
            when (r) {
                Route.Welcome -> WelcomeScreen(onLanguage = { dialog = "language" }, onStart = { go(Route.Intro) })
                Route.Intro -> IntroScreen(onDone = { go(Route.Connect) })
                Route.Connect -> ConnectScreen(onBack = { back() }, pair = { server, code -> pair(server, code) }, onPaired = { replaceAll(Route.Consent) })
                Route.Consent -> {
                    val config = store.config
                    if (config == null) LaunchedEffect(Unit) { replaceAll(Route.Welcome) } else ConsentScreen(
                        config,
                        onReadFull = { go(Route.ConsentText) },
                        onAccepted = {
                            store.consentRead = config.consentVersion ?: "unknown"
                            replaceAll(if (store.hasPin) Route.Permissions else Route.PinSetup)
                        },
                    )
                }
                Route.PinSetup -> PinSetupScreen(onBack = null, onSaved = { store.setPin(it); replaceAll(Route.Permissions) })
                Route.ChangePin -> PinSetupScreen(onBack = { back() }, onSaved = { store.setPin(it); back() }, step = null)
                Route.Permissions -> PermissionsScreen(
                    snapshot,
                    onNotifications = { notifications() },
                    onSites = { sitesOn() },
                    onKeyboard = { keyboardSettings() },
                    onUsage = { usageSettings() },
                    onOverlay = { overlaySettings() },
                    onMessages = { messagesSettings() },
                    onAccessibility = { accessibilitySettings() },
                    onDone = {
                        store.setupDone = true
                        GuardianService.start(context)
                        replaceAll(Route.Main)
                    },
                )
                Route.Main -> Scaffold(bottomBar = { MainBottomBar(tab) { tab = it } }) { padding ->
                    when (tab) {
                        Tab.HOME -> HomeTab(
                            padding, snapshot, store.nudges,
                            onFeature = { go(Route.Detail(it)) },
                            onFix = { tab = Tab.PROTECTION },
                            onTransparency = { go(Route.Transparency) },
                            onAskTime = { askTime() },
                        )
                        Tab.PROTECTION -> ProtectionTab(
                            padding, snapshot,
                            onNotifications = { notifications() },
                            onSites = { on -> if (on) sitesOn() else pinPurpose = "sites_off" },
                            onKeyboard = { if (snapshot.keyboardOn) pinPurpose = "keyboard_off" else keyboardSettings() },
                            onFeature = { go(Route.Detail(it)) },
                            onUsage = { usageSettings() },
                            onOverlay = { overlaySettings() },
                            onMessages = { if (snapshot.messagesOn) pinPurpose = "messages_off" else messagesSettings() },
                            onAccessibility = { if (snapshot.accessibilityOn) pinPurpose = "accessibility_off" else accessibilitySettings() },
                        )
                        Tab.SETTINGS -> {
                            val config = store.config
                            SettingsTab(
                                padding, languageLabel, themeName(theme),
                                DeviceInfo(
                                    server = store.serverUrl.orEmpty(),
                                    nickname = config?.childNickname.orEmpty(),
                                    ageRange = config?.ageRange.orEmpty(),
                                    consentVersion = config?.consentVersion ?: "-",
                                    appVersion = BuildConfig.VERSION_NAME,
                                ),
                                onLanguage = { dialog = "language" },
                                onTheme = { dialog = "theme" },
                                onChangePin = { pinPurpose = "change_pin" },
                                onTransparency = { go(Route.Transparency) },
                                onConsent = { go(Route.ConsentText) },
                                onLicenses = { go(Route.Licenses) },
                                onAbout = { go(Route.About) },
                                onUnpair = { dialog = "unpair" },
                            )
                        }
                    }
                }
                is Route.Detail -> {
                    val f = r.feature
                    val action: Pair<String, () -> Unit>? = when {
                        !snapshot.granted(f) -> null
                        f == Feature.SITUS && !snapshot.sitesOn -> stringResource(R.string.home_sites_enable) to { sitesOn() }
                        f == Feature.LAYAR && !snapshot.accessibilityOn -> stringResource(R.string.perm_accessibility) to { accessibilitySettings() }
                        f == Feature.PAPAN_KETIK && !snapshot.keyboardOn -> stringResource(R.string.home_keyboard_enable) to { keyboardSettings() }
                        f == Feature.WAKTU && !snapshot.usageOn -> stringResource(R.string.perm_usage) to { usageSettings() }
                        f == Feature.WAKTU && !snapshot.overlayOn -> stringResource(R.string.perm_overlay) to { overlaySettings() }
                        f == Feature.WAKTU -> stringResource(R.string.time_request_title) to { askTime() }
                        else -> null
                    }
                    FeatureDetailScreen(f, snapshot.status(f), snapshot.granted(f), action, onBack = { back() })
                }
                Route.Transparency -> TextPage(
                    stringResource(R.string.home_transparency_title), Art.EYE,
                    listOf(R.string.tr_p1, R.string.tr_p2, R.string.tr_p3, R.string.tr_p4, R.string.tr_p5).map { stringResource(it) },
                    onBack = { back() },
                )
                Route.ConsentText -> {
                    val english = LocalConfiguration.current.locales[0].language == "en"
                    val versionLabel = stringResource(R.string.set_consent_version, "%s")
                    LaunchedEffect(english) {
                        val server = store.serverUrl ?: return@LaunchedEffect
                        consentText = runCatching { BackendClient(server) { null }.consentText() }
                            .map { t -> listOf(versionLabel.format(t.version)) + (if (english) t.en else t.id).split("\n").filter { it.isNotBlank() } }
                            .getOrNull()
                    }
                    TextPage(
                        stringResource(R.string.set_consent_text), Art.CONSENT,
                        consentText ?: listOf(stringResource(R.string.consent_loading)),
                        onBack = { back() },
                    )
                }
                Route.About -> AboutScreen(onBack = { back() })
                Route.Licenses -> TextPage(
                    stringResource(R.string.set_licenses), null,
                    listOf(R.string.lic_p1, R.string.lic_p2, R.string.lic_p3, R.string.lic_p4).map { stringResource(it) },
                    onBack = { back() },
                )
            }
        }

        when (dialog) {
            "language" -> ChoiceDialog(
                stringResource(R.string.set_language),
                AppLocale.CHOICES.map { it to languageName(it) },
                AppLocale.current(context),
                onPick = { dialog = null; AppLocale.set(this, it) },
                onDismiss = { dialog = null },
            )
            "theme" -> ChoiceDialog(
                stringResource(R.string.set_theme),
                listOf(UiPrefs.SYSTEM, "light", "dark").map { it to themeName(it) },
                theme,
                onPick = { dialog = null; onTheme(it) },
                onDismiss = { dialog = null },
            )
            "unpair" -> AlertDialog(
                onDismissRequest = { dialog = null },
                title = { Text(stringResource(R.string.set_unpair)) },
                text = { Text(stringResource(R.string.set_unpair_body)) },
                confirmButton = { TextButton(onClick = { dialog = null }) { Text(stringResource(R.string.action_close)) } },
            )
        }

        pinPurpose?.let { purpose ->
            PinDialog(
                title = stringResource(R.string.pin_dialog_title),
                message = stringResource(
                    when (purpose) {
                        "sites_off" -> R.string.pin_dialog_sites_off
                        "keyboard_off" -> R.string.pin_dialog_keyboard_off
                        "messages_off" -> R.string.pin_dialog_messages_off
                        "accessibility_off" -> R.string.pin_dialog_accessibility_off
                        else -> R.string.pin_dialog_change
                    },
                ),
                check = { store.checkPin(it) },
                onDismiss = { pinPurpose = null },
                onConfirmed = {
                    pinPurpose = null
                    when (purpose) {
                        "sites_off" -> {
                            store.sitesEnabled = false
                            SiteGuardVpn.stop(context)
                            refresh++
                        }
                        "keyboard_off" -> keyboardSettings()
                        "messages_off" -> messagesSettings()
                        "accessibility_off" -> accessibilitySettings()
                        "change_pin" -> go(Route.ChangePin)
                    }
                },
            )
        }
    }

    @Composable
    private fun languageName(key: String) = when (key) {
        "id" -> "Bahasa Indonesia"
        "en" -> "English"
        else -> stringResource(R.string.lang_system)
    }

    @Composable
    private fun themeName(key: String) = stringResource(
        when (key) {
            "light" -> R.string.theme_light
            "dark" -> R.string.theme_dark
            else -> R.string.theme_system
        },
    )

    /** Pairs this phone. Returns an error to show, or null on success. */
    private suspend fun pair(server: String, code: String): String? {
        val store = GuardianStore(this)
        return try {
            val response = BackendClient(server) { null }.pair(code, deviceName = Build.MODEL ?: "Android", appVersion = BuildConfig.VERSION_NAME)
            store.serverUrl = server
            store.deviceToken = response.deviceToken
            store.config = response.config
            ServiceLocator.reset()
            null
        } catch (_: BackendException) {
            getString(R.string.setup_error)
        } catch (_: Exception) {
            getString(R.string.setup_neterror)
        }
    }
}
