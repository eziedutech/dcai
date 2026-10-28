package dev.eziedutech.dcai.guardian.ui

import androidx.compose.foundation.background
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
import androidx.compose.material.icons.rounded.Badge
import androidx.compose.material.icons.rounded.DarkMode
import androidx.compose.material.icons.rounded.Dns
import androidx.compose.material.icons.rounded.Gavel
import androidx.compose.material.icons.rounded.Home
import androidx.compose.material.icons.rounded.Info
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
    NavigationBar(containerColor = MaterialTheme.colorScheme.surface) {
        Tab.entries.forEach { t ->
            NavigationBarItem(selected = t == tab, onClick = { onTab(t) }, icon = { Icon(t.icon, null) }, label = { Text(stringResource(t.label)) })
        }
    }
}

@Composable
private fun TabColumn(padding: PaddingValues, content: @Composable () -> Unit) {
    Column(
        Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).padding(padding)
            .verticalScroll(rememberScrollState()).padding(horizontal = 20.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) { content() }
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
    Box(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(28.dp))
            .background(Brush.linearGradient(if (ok) listOf(BrandBlue, Color(0xFF2B63D1), BrandLeaf) else listOf(Color(0xFF9A5B00), Color(0xFFE29A2E))))
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
            Illustration(if (ok) Art.SHIELD else Art.SHIELD_WARN, Modifier.size(112.dp))
        }
    }
}

@Composable
private fun FeatureTile(feature: Feature, status: Status, modifier: Modifier, onClick: () -> Unit) {
    Card(
        modifier.clickable(onClick = onClick), shape = RoundedCornerShape(22.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            IconBubble(feature.icon)
            Text(stringResource(feature.title), style = MaterialTheme.typography.titleMedium)
            StatusPill(status)
        }
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
        Modifier.fillMaxWidth().clip(RoundedCornerShape(22.dp)).background(MaterialTheme.colorScheme.tertiaryContainer).padding(16.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Illustration(Art.TIP, Modifier.size(64.dp))
        Spacer(Modifier.width(12.dp))
        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(stringResource(R.string.home_tip), style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onTertiaryContainer)
            Text(stringResource(tip), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onTertiaryContainer)
        }
    }
}

@Composable
private fun InfoBanner(art: Art, title: String, body: String, onClick: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(22.dp)).background(MaterialTheme.colorScheme.primaryContainer)
            .clickable(onClick = onClick).padding(16.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Illustration(art, Modifier.size(64.dp))
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.onPrimaryContainer)
            Text(body, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onPrimaryContainer)
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
    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).safeDrawingPadding()) {
        BackHeader(stringResource(feature.title), onBack)
        Column(
            Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(horizontal = 20.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Illustration(feature.art, Modifier.fillMaxWidth(0.6f).align(Alignment.CenterHorizontally))
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
    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).safeDrawingPadding()) {
        BackHeader(title, onBack)
        Column(
            Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(horizontal = 20.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            if (art != null) Illustration(art, Modifier.fillMaxWidth(0.5f).align(Alignment.CenterHorizontally))
            paragraphs.forEach { Text(it, style = MaterialTheme.typography.bodyLarge) }
            Spacer(Modifier.height(16.dp))
        }
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
