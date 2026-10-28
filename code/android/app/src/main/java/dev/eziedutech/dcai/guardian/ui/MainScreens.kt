package dev.eziedutech.dcai.guardian.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.MenuBook
import androidx.compose.material.icons.rounded.Apps
import androidx.compose.material.icons.rounded.Badge
import androidx.compose.material.icons.rounded.DarkMode
import androidx.compose.material.icons.rounded.Dns
import androidx.compose.material.icons.rounded.Gavel
import androidx.compose.material.icons.rounded.Home
import androidx.compose.material.icons.rounded.Info
import androidx.compose.material.icons.rounded.Layers
import androidx.compose.material.icons.rounded.LinkOff
import androidx.compose.material.icons.rounded.Lock
import androidx.compose.material.icons.rounded.Notifications
import androidx.compose.material.icons.rounded.Settings
import androidx.compose.material.icons.rounded.Shield
import androidx.compose.material.icons.rounded.Translate
import androidx.compose.material.icons.rounded.Visibility
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import dev.eziedutech.dcai.guardian.R
import dev.eziedutech.dcai.guardian.data.Nudge
import dev.eziedutech.dcai.guardian.ui.art.Art
import dev.eziedutech.dcai.guardian.ui.art.Illustration
import dev.eziedutech.dcai.guardian.ui.theme.BrandBlue
import dev.eziedutech.dcai.guardian.ui.theme.BrandLeaf
import java.text.DateFormat
import java.util.Calendar
import java.util.Date

enum class Tab(val icon: androidx.compose.ui.graphics.vector.ImageVector, val label: Int) {
    HOME(Icons.Rounded.Home, R.string.tab_home),
    PROTECTION(Icons.Rounded.Shield, R.string.tab_protection),
    SETTINGS(Icons.Rounded.Settings, R.string.tab_settings),
}

@Composable
fun MainBottomBar(tab: Tab, onTab: (Tab) -> Unit) {
    NavigationBar(containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.92f), tonalElevation = 0.dp) {
        Tab.entries.forEach { t ->
            NavigationBarItem(selected = t == tab, onClick = { onTab(t) }, icon = { Icon(t.icon, null) }, label = { Text(stringResource(t.label)) })
        }
    }
}

@Composable
private fun TabColumn(padding: PaddingValues, content: @Composable () -> Unit) {
    val scroll = rememberScrollState()
    GlassScene(scroll, Modifier.padding(padding)) {
        Column(
            Modifier.fillMaxSize().verticalScroll(scroll).padding(horizontal = 20.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) { content() }
    }
}

// ------------------------------------------------------------------ home

@Composable
fun HomeTab(
    padding: PaddingValues,
    snapshot: Snapshot,
    nudges: List<Nudge>,
    onFeature: (Feature) -> Unit,
    onFix: () -> Unit,
    onTransparency: () -> Unit,
    onAskTime: () -> Unit = {},
) {
    val nickname = snapshot.config?.childNickname.orEmpty()
    TabColumn(padding) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            LogoBadge(44.dp)
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(stringResource(R.string.brand_title), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.ExtraBold)
                Text(stringResource(R.string.brand_subtitle), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }

        HeroCard(nickname, snapshot.issues, onFix)

        if (snapshot.granted(Feature.WAKTU)) TodayCard(snapshot.today, onAskTime)

        SectionTitle(stringResource(R.string.home_features))
        Feature.entries.chunked(2).forEach { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                row.forEach { f -> FeatureTile(f, snapshot.status(f), Modifier.weight(1f)) { onFeature(f) } }
                if (row.size == 1) Spacer(Modifier.weight(1f))
            }
        }

        SectionTitle(stringResource(R.string.home_nudges))
        NudgeCard(nudges)

        TipCard()

        InfoBanner(Art.EYE, stringResource(R.string.home_transparency_title), stringResource(R.string.home_transparency_short), onTransparency)
    }
}

@Composable
private fun HeroCard(nickname: String, issues: Int, onFix: () -> Unit) {
    val ok = issues == 0
    val scroll = LocalScroll.current
    val shape = RoundedCornerShape(28.dp)
    val glow = if (ok) BrandLeaf else Color(0xFFFFC76E)
    Box(
        Modifier.fillMaxWidth().clip(shape)
            .background(Brush.linearGradient(if (ok) listOf(Color(0xFF173A8A), BrandBlue) else listOf(Color(0xFF7A4A06), Color(0xFFA9680F))))
            .background(Brush.radialGradient(listOf(glow.copy(alpha = 0.42f), Color.Transparent), center = Offset(Float.POSITIVE_INFINITY, Float.POSITIVE_INFINITY), radius = 720f))
            .border(1.dp, Color.White.copy(alpha = 0.16f), shape)
            .clickable(enabled = !ok, onClick = onFix).padding(20.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(
                    if (nickname.isNotBlank()) stringResource(R.string.home_hello, nickname) else stringResource(R.string.home_hello_plain),
                    style = MaterialTheme.typography.titleMedium, color = Color.White.copy(alpha = 0.9f),
                )
                Text(
                    stringResource(if (ok) R.string.home_protected else R.string.home_attention),
                    style = MaterialTheme.typography.headlineSmall, color = Color.White,
                )
                Text(
                    if (ok) stringResource(R.string.home_protected_sub) else pluralStringResource(R.plurals.home_attention_sub, issues, issues),
                    style = MaterialTheme.typography.bodyMedium, color = Color.White.copy(alpha = 0.9f),
                )
            }
            Illustration(if (ok) Art.SHIELD else Art.SHIELD_WARN, Modifier.size(112.dp).parallax(scroll, 0.12f))
        }
    }
}

@Composable
private fun TodayCard(today: dev.eziedutech.dcai.guardian.screen.TodayState?, onAskTime: () -> Unit) {
    GroupCard {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Illustration(Art.CLOCK, Modifier.size(56.dp))
                Spacer(Modifier.width(12.dp))
                Column(Modifier.weight(1f)) {
                    Text(stringResource(R.string.home_today_title), style = MaterialTheme.typography.titleMedium)
                    val line = when {
                        today == null -> stringResource(R.string.home_today_setup)
                        today.inBedtime -> stringResource(R.string.home_today_bedtime_now)
                        today.leftMinutes != null -> stringResource(R.string.home_today_left, hm(today.leftMinutes!!))
                        else -> stringResource(R.string.home_today_used_only, hm(today.usedMinutes))
                    }
                    Text(line, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            val limit = today?.limitMinutes
            if (today != null && limit != null) {
                val total = (limit + today.bonusMinutes).coerceAtLeast(1)
                androidx.compose.material3.LinearProgressIndicator(
                    progress = { (today.usedMinutes.toFloat() / total).coerceIn(0f, 1f) },
                    modifier = Modifier.fillMaxWidth().height(10.dp).clip(RoundedCornerShape(5.dp)),
                    color = MaterialTheme.colorScheme.secondary,
                )
                Text(
                    stringResource(R.string.home_today_used, hm(today.usedMinutes), hm(total)) +
                        (today.bedtimeStart?.let { "  ·  " + stringResource(R.string.home_today_bedtime, it) } ?: ""),
                    style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            androidx.compose.material3.TextButton(onClick = onAskTime) { Text(stringResource(R.string.time_request_title)) }
        }
    }
}

@Composable
private fun hm(minutes: Int): String {
    val h = minutes / 60
    val m = minutes % 60
    return if (h > 0) stringResource(R.string.duration_hm, h, m) else stringResource(R.string.duration_m, m)
}

@Composable
private fun FeatureTile(feature: Feature, status: Status, modifier: Modifier, onClick: () -> Unit) {
    Column(
        modifier.glass(RoundedCornerShape(22.dp)).clickable(onClick = onClick).padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        IconBubble(feature.icon)
        Text(stringResource(feature.title), style = MaterialTheme.typography.titleMedium)
        StatusPill(status)
    }
}

@Composable
private fun NudgeCard(nudges: List<Nudge>) {
    GroupCard {
        if (nudges.isEmpty()) {
            Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                Illustration(Art.NUDGE, Modifier.size(72.dp))
                Spacer(Modifier.width(12.dp))
                Text(stringResource(R.string.home_nudges_empty), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        } else {
            nudges.take(3).forEachIndexed { i, n ->
                if (i > 0) HorizontalDivider(Modifier.padding(horizontal = 16.dp), color = MaterialTheme.colorScheme.outlineVariant)
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(n.text, style = MaterialTheme.typography.bodyMedium)
                    Text(
                        DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.SHORT).format(Date(n.at)),
                        style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
    }
}

@Composable
private fun TipCard() {
    val tips = listOf(R.string.tip1, R.string.tip2, R.string.tip3, R.string.tip4, R.string.tip5, R.string.tip6)
    val tip = tips[Calendar.getInstance().get(Calendar.DAY_OF_YEAR) % tips.size]
    Row(
        Modifier.fillMaxWidth().glass(RoundedCornerShape(22.dp)).background(MaterialTheme.colorScheme.tertiaryContainer.copy(alpha = 0.35f)).padding(16.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Illustration(Art.TIP, Modifier.size(64.dp))
        Spacer(Modifier.width(12.dp))
        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(stringResource(R.string.home_tip), style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.tertiary)
            Text(stringResource(tip), style = MaterialTheme.typography.bodyMedium)
        }
    }
}

@Composable
private fun InfoBanner(art: Art, title: String, body: String, onClick: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().glass(RoundedCornerShape(22.dp)).background(MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f))
            .clickable(onClick = onClick).padding(16.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Illustration(art, Modifier.size(64.dp))
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Text(body, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

// ------------------------------------------------------------------ protection

@Composable
fun ProtectionTab(
    padding: PaddingValues,
    snapshot: Snapshot,
    onNotifications: () -> Unit,
    onSites: (Boolean) -> Unit,
    onKeyboard: () -> Unit,
    onFeature: (Feature) -> Unit,
    onUsage: () -> Unit = {},
    onOverlay: () -> Unit = {},
) {
    TabColumn(padding) {
        Text(stringResource(R.string.tab_protection), style = MaterialTheme.typography.headlineMedium)
        Text(stringResource(R.string.prot_lead), color = MaterialTheme.colorScheme.onSurfaceVariant)

        SectionTitle(stringResource(R.string.prot_on_phone))
        GroupCard {
            SwitchRow(
                Icons.Rounded.Notifications, stringResource(R.string.perm_notifications), stringResource(R.string.perm_notifications_sub),
                if (snapshot.notificationsOn) Status.ON else Status.NEEDS_SETUP, snapshot.notificationsOn,
            ) { onNotifications() }
            HorizontalDivider(Modifier.padding(horizontal = 16.dp), color = MaterialTheme.colorScheme.outlineVariant)
            SwitchRow(
                Feature.SITUS.icon, stringResource(R.string.f_site), stringResource(R.string.f_site_short),
                snapshot.status(Feature.SITUS), snapshot.sitesOn, enabled = snapshot.granted(Feature.SITUS),
            ) { onSites(it) }
            HorizontalDivider(Modifier.padding(horizontal = 16.dp), color = MaterialTheme.colorScheme.outlineVariant)
            SwitchRow(
                Feature.PAPAN_KETIK.icon, stringResource(R.string.f_keyboard), stringResource(R.string.f_keyboard_short),
                snapshot.status(Feature.PAPAN_KETIK), snapshot.keyboardOn, enabled = snapshot.granted(Feature.PAPAN_KETIK),
            ) { onKeyboard() }
            if (snapshot.granted(Feature.WAKTU)) {
                HorizontalDivider(Modifier.padding(horizontal = 16.dp), color = MaterialTheme.colorScheme.outlineVariant)
                SwitchRow(
                    Feature.WAKTU.icon, stringResource(R.string.perm_usage), stringResource(R.string.perm_usage_sub),
                    if (snapshot.usageOn) Status.ON else Status.NEEDS_SETUP, snapshot.usageOn,
                ) { onUsage() }
                HorizontalDivider(Modifier.padding(horizontal = 16.dp), color = MaterialTheme.colorScheme.outlineVariant)
                SwitchRow(
                    Icons.Rounded.Layers, stringResource(R.string.perm_overlay), stringResource(R.string.perm_overlay_sub),
                    if (snapshot.overlayOn) Status.ON else Status.NEEDS_SETUP, snapshot.overlayOn,
                ) { onOverlay() }
            }
        }
        Text(stringResource(R.string.prot_off_note), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)

        SectionTitle(stringResource(R.string.prot_from_parent))
        GroupCard {
            Feature.entries.forEachIndexed { i, f ->
                if (i > 0) HorizontalDivider(Modifier.padding(horizontal = 16.dp), color = MaterialTheme.colorScheme.outlineVariant)
                SettingRow(
                    f.icon, stringResource(f.title),
                    stringResource(if (snapshot.granted(f)) R.string.prot_granted else R.string.prot_not_granted),
                    onClick = { onFeature(f) },
                    trailing = { StatusPill(snapshot.status(f)) },
                )
            }
        }
        if (snapshot.granted(Feature.GAMBAR) && !snapshot.sensitiveModel) {
            Text(stringResource(R.string.home_images_model_off), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

// ------------------------------------------------------------------ settings

data class DeviceInfo(val server: String, val nickname: String, val ageRange: String, val consentVersion: String, val appVersion: String)

@Composable
fun SettingsTab(
    padding: PaddingValues,
    languageLabel: String,
    themeLabel: String,
    info: DeviceInfo,
    onLanguage: () -> Unit,
    onTheme: () -> Unit,
    onChangePin: () -> Unit,
    onTransparency: () -> Unit,
    onConsent: () -> Unit,
    onLicenses: () -> Unit,
    onUnpair: () -> Unit,
    onAbout: () -> Unit = {},
) {
    TabColumn(padding) {
        Text(stringResource(R.string.tab_settings), style = MaterialTheme.typography.headlineMedium)

        SectionTitle(stringResource(R.string.set_general))
        GroupCard {
            SettingRow(Icons.Rounded.Translate, stringResource(R.string.set_language), languageLabel, onLanguage)
            SettingRow(Icons.Rounded.DarkMode, stringResource(R.string.set_theme), themeLabel, onTheme)
        }

        SectionTitle(stringResource(R.string.set_security))
        GroupCard {
            SettingRow(Icons.Rounded.Lock, stringResource(R.string.set_pin), stringResource(R.string.set_pin_sub), onChangePin)
        }

        SectionTitle(stringResource(R.string.set_device))
        GroupCard {
            SettingRow(Icons.Rounded.Badge, stringResource(R.string.set_for), "${info.nickname} · ${info.ageRange}", trailing = null)
            SettingRow(Icons.Rounded.Dns, stringResource(R.string.set_server), info.server, trailing = null)
            SettingRow(Icons.Rounded.Info, stringResource(R.string.set_version), "${info.appVersion} · ${stringResource(R.string.set_consent_version, info.consentVersion)}", trailing = null)
        }

        SectionTitle(stringResource(R.string.set_info))
        GroupCard {
            SettingRow(Icons.Rounded.Visibility, stringResource(R.string.home_transparency_title), null, onTransparency)
            SettingRow(Icons.AutoMirrored.Rounded.MenuBook, stringResource(R.string.set_consent_text), null, onConsent)
            SettingRow(Icons.Rounded.Gavel, stringResource(R.string.set_licenses), null, onLicenses)
            SettingRow(Icons.Rounded.Apps, stringResource(R.string.about_title), null, onAbout)
        }

        GroupCard {
            SettingRow(Icons.Rounded.LinkOff, stringResource(R.string.set_unpair), stringResource(R.string.set_unpair_sub), onUnpair)
        }
        Spacer(Modifier.height(8.dp))
    }
}

// ------------------------------------------------------------------ detail and text pages

@Composable
fun BackHeader(title: String, onBack: () -> Unit) {
    Row(Modifier.fillMaxWidth().padding(horizontal = 4.dp, vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
        IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Rounded.ArrowBack, stringResource(R.string.action_back)) }
        Text(title, style = MaterialTheme.typography.titleLarge)
    }
}

@Composable
fun FeatureDetailScreen(feature: Feature, status: Status, granted: Boolean, action: Pair<String, () -> Unit>?, onBack: () -> Unit) {
    val scroll = rememberScrollState()
    GlassScene(scroll) {
        Column(Modifier.fillMaxSize().safeDrawingPadding()) {
            BackHeader(stringResource(feature.title), onBack)
            Column(
                Modifier.weight(1f).verticalScroll(scroll).padding(horizontal = 20.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                // The picture drifts slower than the text.
                Illustration(feature.art, Modifier.fillMaxWidth(0.6f).align(Alignment.CenterHorizontally).parallax(LocalScroll.current, 0.35f))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(stringResource(feature.short), style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                    StatusPill(status)
                }
                DetailBlock(stringResource(R.string.detail_what), stringResource(feature.what))
                DetailBlock(stringResource(R.string.detail_stays), stringResource(feature.stays))
                DetailBlock(stringResource(R.string.detail_sent), stringResource(feature.sent))
                if (!granted) DetailBlock(stringResource(R.string.detail_not_granted_title), stringResource(R.string.detail_not_granted))
                action?.let { (label, run) -> PrimaryButton(label, run) }
                Spacer(Modifier.height(12.dp))
            }
        }
    }
}

@Composable
private fun DetailBlock(title: String, body: String) {
    GroupCard {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(title, style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
            Text(body, style = MaterialTheme.typography.bodyMedium)
        }
    }
}

/** A long text (transparency, consent, licenses), with an illustration on top. */
@Composable
fun TextPage(title: String, art: Art?, paragraphs: List<String>, onBack: () -> Unit) {
    val scroll = rememberScrollState()
    GlassScene(scroll) {
        Column(Modifier.fillMaxSize().safeDrawingPadding()) {
            BackHeader(title, onBack)
            Column(
                Modifier.weight(1f).verticalScroll(scroll).padding(horizontal = 20.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                if (art != null) Illustration(art, Modifier.fillMaxWidth(0.5f).align(Alignment.CenterHorizontally).parallax(LocalScroll.current, 0.35f))
                Column(Modifier.fillMaxWidth().glass().padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    paragraphs.forEach { Text(it, style = MaterialTheme.typography.bodyLarge) }
                }
                Spacer(Modifier.height(16.dp))
            }
        }
    }
}

/** Who makes dcAI and the platforms beside it. */
@Composable
fun AboutScreen(onBack: () -> Unit) {
    val scroll = rememberScrollState()
    GlassScene(scroll) {
        Column(Modifier.fillMaxSize().safeDrawingPadding()) {
            BackHeader(stringResource(R.string.about_title), onBack)
            Column(
                Modifier.weight(1f).verticalScroll(scroll).padding(horizontal = 20.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                LogoBadge(84.dp, Modifier.align(Alignment.CenterHorizontally).parallax(LocalScroll.current, 0.3f))
                Text(
                    "\u201C" + stringResource(R.string.about_tagline) + "\u201D",
                    style = MaterialTheme.typography.titleMedium, fontStyle = androidx.compose.ui.text.font.FontStyle.Italic,
                    color = MaterialTheme.colorScheme.onSurfaceVariant, textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                    modifier = Modifier.fillMaxWidth(),
                )
                Text(stringResource(R.string.about_lead), style = MaterialTheme.typography.bodyLarge)
                SectionTitle(stringResource(R.string.about_eco))
                Platform("dcAI", stringResource(R.string.brand_title) + ", " + stringResource(R.string.brand_subtitle), stringResource(R.string.about_dcai), stringResource(R.string.about_here))
                Platform("C.I.T.R.A.", "Core Integrity & Trustworthy Research Assistant", stringResource(R.string.about_citra))
                Platform("Belajar Z", null, stringResource(R.string.about_bz))
                Platform("Numeria Arena", null, stringResource(R.string.about_numeria))
                Spacer(Modifier.height(12.dp))
            }
        }
    }
}

@Composable
private fun Platform(name: String, full: String?, body: String, badge: String? = null) {
    Column(Modifier.fillMaxWidth().glass(RoundedCornerShape(22.dp)).padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(name, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
            if (badge != null) {
                Text(
                    badge, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onPrimary,
                    modifier = Modifier.clip(RoundedCornerShape(50)).background(MaterialTheme.colorScheme.primary).padding(horizontal = 10.dp, vertical = 3.dp),
                )
            }
        }
        if (full != null) Text(full, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(body, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 4.dp))
    }
}

@Composable
fun ChoiceDialog(title: String, options: List<Pair<String, String>>, selected: String, onPick: (String) -> Unit, onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = {
            Column {
                options.forEach { (key, label) ->
                    Row(
                        Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp)).clickable { onPick(key) }.padding(vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        RadioButton(selected = key == selected, onClick = { onPick(key) })
                        Text(label)
                    }
                }
            }
        },
        confirmButton = { TextButton(onClick = onDismiss) { Text(stringResource(R.string.action_close)) } },
    )
}
