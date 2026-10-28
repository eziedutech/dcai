package dev.eziedutech.dcai.guardian.sites

import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.eziedutech.dcai.guardian.R
import dev.eziedutech.dcai.guardian.ServiceLocator
import dev.eziedutech.dcai.guardian.net.DetectionFeedbackRequest
import dev.eziedutech.dcai.guardian.service.Notifications
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * A held site, reviewed with the parent on the child's phone. With the PIN the parent can
 * allow it on this phone. The server then gets a note of a false detection with the
 * category only; the site's name stays on the phone.
 */
class SiteReviewActivity : dev.eziedutech.dcai.guardian.ui.LocalizedActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val site = intent.getStringExtra(EXTRA_SITE)?.let(SiteNames::normalise)
        val category = intent.getStringExtra(EXTRA_CATEGORY)?.takeIf { it.matches(Regex("^[a-z]{3,20}$")) }
        if (site == null || category == null) {
            finish()
            return
        }
        val store = ServiceLocator.store(this)
        setContent {
            dev.eziedutech.dcai.guardian.ui.theme.DcaiTheme(dev.eziedutech.dcai.guardian.ui.UiPrefs(this).theme) {
                Surface(Modifier.fillMaxSize()) {
                    val scope = rememberCoroutineScope()
                    var pin by remember { mutableStateOf("") }
                    var attempts by remember { mutableIntStateOf(0) }
                    var error by remember { mutableStateOf(false) }
                    var busy by remember { mutableStateOf(false) }
                    Column(
                        Modifier.fillMaxSize().safeDrawingPadding().padding(24.dp),
                        verticalArrangement = Arrangement.spacedBy(16.dp),
                    ) {
                        Text(stringResource(R.string.review_title), fontSize = 24.sp, fontWeight = FontWeight.ExtraBold)
                        Text(stringResource(R.string.site_review_lead, site, Notifications.siteCategoryLabel(this@SiteReviewActivity, category)))
                        if (!store.hasPin) {
                            Text(stringResource(R.string.review_no_pin))
                        } else {
                            OutlinedTextField(
                                value = pin, onValueChange = { pin = it.filter(Char::isDigit).take(8) },
                                label = { Text(stringResource(R.string.review_pin)) },
                                singleLine = true, modifier = Modifier.fillMaxWidth(),
                                visualTransformation = PasswordVisualTransformation(),
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
                            )
                            if (error) Text(stringResource(R.string.review_wrong_pin), color = MaterialTheme.colorScheme.error)
                            Button(
                                onClick = {
                                    busy = true
                                    scope.launch {
                                        val ok = withContext(Dispatchers.Default) { store.checkPin(pin) }
                                        pin = ""
                                        if (ok) {
                                            allow(site, category)
                                            finish()
                                        } else {
                                            error = true
                                            if (++attempts >= MAX_ATTEMPTS) finish()
                                        }
                                        busy = false
                                    }
                                },
                                enabled = !busy && pin.length >= 4,
                                modifier = Modifier.fillMaxWidth(),
                            ) { Text(stringResource(R.string.site_review_allow)) }
                        }
                        OutlinedButton(onClick = { finish() }, modifier = Modifier.fillMaxWidth()) {
                            Text(stringResource(R.string.site_review_keep))
                        }
                    }
                }
            }
        }
    }

    private suspend fun allow(site: String, category: String) {
        ServiceLocator.store(this).allowSite(SiteMatcher.hex(SiteNames.hash(site)))
        SiteGuardVpn.reload(this)
        val client = ServiceLocator.client(this) ?: return
        val version = SiteLists(this, client).manifest()?.version ?: return
        runCatching {
            client.sendDetectionFeedback(
                DetectionFeedbackRequest(kind = "domain", category = category, score = 100, modelVersion = "ut1-$version"),
            )
        }
    }

    companion object {
        const val EXTRA_SITE = "site"
        const val EXTRA_CATEGORY = "category"
        private const val MAX_ATTEMPTS = 5
    }
}
