package dev.eziedutech.dcai.guardian.screen

import android.content.Intent
import android.os.Bundle
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import dev.eziedutech.dcai.guardian.R
import dev.eziedutech.dcai.guardian.ServiceLocator
import dev.eziedutech.dcai.guardian.net.TimeRequestBody
import dev.eziedutech.dcai.guardian.net.TimeRequestContext
import dev.eziedutech.dcai.guardian.privacy.Mask
import dev.eziedutech.dcai.guardian.service.Notifications
import dev.eziedutech.dcai.guardian.ui.CenteredText
import dev.eziedutech.dcai.guardian.ui.GlassScene
import dev.eziedutech.dcai.guardian.ui.LocalScroll
import dev.eziedutech.dcai.guardian.ui.glass
import dev.eziedutech.dcai.guardian.ui.parallax
import dev.eziedutech.dcai.guardian.ui.LocalizedActivity
import dev.eziedutech.dcai.guardian.ui.PrimaryButton
import dev.eziedutech.dcai.guardian.ui.UiPrefs
import dev.eziedutech.dcai.guardian.ui.art.Art
import dev.eziedutech.dcai.guardian.ui.art.Illustration
import dev.eziedutech.dcai.guardian.ui.theme.DcaiTheme
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.time.LocalDateTime

/**
 * The break screen: bedtime, the day's time used up, or a pause from short video. It
 * explains why, counts down a break, and lets the child ask the parent for more time.
 * Opened without a reason, it is only the request.
 */
class TimeOutActivity : LocalizedActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val reason = intent.getStringExtra(EXTRA_REASON)?.let { r -> BlockReason.entries.firstOrNull { it.name == r } }
        val category = intent.getStringExtra(EXTRA_CATEGORY)
        val until = intent.getLongExtra(EXTRA_UNTIL, 0L)
        setContent {
            DcaiTheme(UiPrefs(this).theme) {
                Surface(Modifier.fillMaxSize()) {
                    TimeOutScreen(reason, category, until, onHome = ::goHome, onClose = { finish() })
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        visible = true
    }

    override fun onPause() {
        visible = false
        super.onPause()
    }

    private fun goHome() {
        startActivity(Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        finish()
    }

    companion object {
        const val EXTRA_REASON = "reason"
        const val EXTRA_CATEGORY = "category"
        const val EXTRA_UNTIL = "until"

        @Volatile var visible = false
            private set
    }
}

@Composable
private fun TimeOutScreen(reason: BlockReason?, category: String?, until: Long, onHome: () -> Unit, onClose: () -> Unit) {
    val context = androidx.compose.ui.platform.LocalContext.current
    val store = remember { ServiceLocator.store(context) }
    val scope = rememberCoroutineScope()
    var now by remember { mutableLongStateOf(System.currentTimeMillis()) }
    var minutes by remember { mutableIntStateOf(15) }
    var note by remember { mutableStateOf("") }
    var pending by remember { mutableStateOf(store.pendingTimeRequest != null) }
    var error by remember { mutableStateOf(false) }
    val decisions by ScreenGuard.decisions.collectAsState()
    val focus = androidx.compose.ui.platform.LocalFocusManager.current

    // A break ends by itself; a decision from the parent closes the screen too.
    LaunchedEffect(until) {
        while (true) {
            now = System.currentTimeMillis()
            if (until > 0 && now >= until) onClose()
            delay(1000)
        }
    }
    LaunchedEffect(decisions) {
        if (decisions > 0 && pending && store.pendingTimeRequest == null) onClose()
    }
    BackHandler { if (reason == null) onClose() else onHome() }

    val categoryLabel = category?.let { stringResource(categoryName(it)) }
    val (art, title) = when (reason) {
        BlockReason.BEDTIME -> Art.MOON to stringResource(R.string.timeout_bedtime)
        BlockReason.DAILY -> Art.CLOCK to stringResource(R.string.timeout_daily)
        BlockReason.CATEGORY -> Art.CLOCK to stringResource(R.string.timeout_category, categoryLabel ?: "")
        BlockReason.SESSION -> Art.BREAK to stringResource(R.string.timeout_session)
        BlockReason.APP_NOT_ALLOWED -> Art.CLOCK to stringResource(R.string.timeout_app)
        null -> Art.CLOCK to stringResource(R.string.time_request_title)
    }

    val scroll = rememberScrollState()
    GlassScene(scroll) {
        Column(
            Modifier.fillMaxSize().safeDrawingPadding().imePadding()
                .verticalScroll(scroll).padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Illustration(art, Modifier.fillMaxWidth(0.55f).parallax(LocalScroll.current, 0.35f))
            Text(title, style = MaterialTheme.typography.headlineMedium, textAlign = TextAlign.Center)
            if (reason != null) CenteredText(stringResource(Notifications.timeOutText(reason)))
            if (reason == BlockReason.SESSION && until > now) {
                val left = ((until - now) / 1000).toInt()
                Text("%d:%02d".format(left / 60, left % 60), style = MaterialTheme.typography.displayMedium, color = MaterialTheme.colorScheme.primary)
            }

            Column(
                Modifier.fillMaxWidth().glass(RoundedCornerShape(22.dp), strong = true).padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                if (pending) {
                    Text(stringResource(R.string.time_request_waiting), style = MaterialTheme.typography.titleMedium)
                    Text(stringResource(R.string.time_request_waiting_sub), color = MaterialTheme.colorScheme.onSurfaceVariant)
                } else {
                    Text(stringResource(R.string.time_request_ask), style = MaterialTheme.typography.titleMedium)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        listOf(15, 30, 60).forEach { m ->
                            FilterChip(selected = minutes == m, onClick = { minutes = m }, label = { Text(stringResource(R.string.time_minutes, m)) })
                        }
                    }
                    OutlinedTextField(
                        value = note, onValueChange = { note = it.take(200) },
                        label = { Text(stringResource(R.string.time_request_reason)) },
                        modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(14.dp),
                        singleLine = true,
                        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                        keyboardActions = KeyboardActions(onDone = { focus.clearFocus() }),
                    )
                    if (error) Text(stringResource(R.string.setup_neterror), color = MaterialTheme.colorScheme.error)
                    PrimaryButton(stringResource(R.string.time_request_send), onClick = {
                        scope.launch {
                            val client = ServiceLocator.client(context) ?: return@launch
                            val config = store.config
                            val policy = config?.screenPolicy
                            val today = ScreenGuard.today
                            // Masked here; the server masks again.
                            val names = listOfNotNull(config?.childNickname).filter { it.isNotBlank() }
                            val body = TimeRequestBody(
                                minutes = minutes,
                                reason = Mask.mask(note, names).text.take(200),
                                context = TimeRequestContext(
                                    usedToday = today?.usedMinutes ?: 0,
                                    limitToday = today?.limitMinutes,
                                    category = category,
                                    minutesToBedtime = policy?.let { TimeRules.minutesToBedtime(it, LocalDateTime.now()) },
                                ),
                            )
                            runCatching { client.requestTime(body) }
                                .onSuccess { store.pendingTimeRequest = it.id; pending = true; error = false }
                                .onFailure { error = true }
                        }
                    })
                }
            }
            OutlinedButton(onClick = if (reason == null) onClose else onHome, modifier = Modifier.fillMaxWidth()) {
                Text(stringResource(if (reason == null) R.string.action_close else R.string.timeout_home))
            }
        }
    }
}

fun categoryName(wire: String): Int = when (wire) {
    "video" -> R.string.cat_video
    "game" -> R.string.cat_game
    "sosial" -> R.string.cat_sosial
    else -> R.string.cat_lain
}
