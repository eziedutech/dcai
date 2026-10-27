package dev.eziedutech.dcai.samplechat

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.platform.LocalContext
import androidx.compose.runtime.LaunchedEffect

/** One turn of the synthetic scenario. Synthetic data only. */
private data class Turn(val sender: String, val text: String)

// A short staged-approach scenario a contact might use. Synthetic, for testing dcAI.
private val SCENARIO = listOf(
    Turn("contact", "halo, kamu jago banget mainnya, beda dari yang lain"),
    Turn("contact", "main bareng yuk tiap hari, nanti aku ajarin trik"),
    Turn("contact", "aku kasih skin gratis, tapi jangan bilang siapa-siapa ya"),
    Turn("contact", "kirim foto kamu dong, terus kita lanjut ngobrol di aplikasi lain"),
)

private const val CHANNEL = "game_chat"
private const val THREAD = "gamechat-newfriend-001"

private val Purple = Color(0xFF4C1D95)
private val Bubble = Color(0xFFEDE7F6)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MaterialTheme {
                Surface(Modifier.fillMaxSize()) { ChatScreen() }
            }
        }
    }
}

@Composable
private fun ChatScreen() {
    val context = LocalContext.current
    val messages = remember { mutableStateListOf<Turn>() }
    var step by remember { mutableIntStateOf(0) }
    var draft by remember { mutableStateOf("") }
    val listState = rememberLazyListState()
    val linked = remember { dcaiInstalled(context) }

    fun send(turn: Turn, contactKnown: Boolean) {
        messages.add(turn)
        sendToDcai(context, turn, contactKnown)
    }

    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) listState.animateScrollToItem(messages.size - 1)
    }

    Column(Modifier.fillMaxSize().safeDrawingPadding()) {
        Column(Modifier.fillMaxWidth().background(Purple).padding(16.dp)) {
            Text(stringRes(context, R.string.contact), color = Color.White, fontWeight = FontWeight.Bold, fontSize = 18.sp)
            Text(
                stringRes(context, if (linked) R.string.linked else R.string.not_linked),
                color = Color.White.copy(alpha = 0.85f), fontSize = 12.sp,
            )
        }

        LazyColumn(
            state = listState,
            modifier = Modifier.weight(1f).fillMaxWidth().padding(horizontal = 12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            items(messages) { turn -> MessageBubble(turn) }
        }

        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            if (step < SCENARIO.size) {
                Button(onClick = { send(SCENARIO[step], contactKnown = false); step++ }, modifier = Modifier.fillMaxWidth()) {
                    Text(stringRes(context, R.string.play_next))
                }
            } else {
                Text(stringRes(context, R.string.done), color = Purple, fontWeight = FontWeight.Bold)
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                OutlinedTextField(
                    value = draft, onValueChange = { draft = it },
                    placeholder = { Text(stringRes(context, R.string.type_hint)) },
                    singleLine = true, modifier = Modifier.weight(1f),
                )
                Button(onClick = {
                    val text = draft.trim()
                    if (text.isNotEmpty()) {
                        send(Turn("child", text), contactKnown = false)
                        draft = ""
                    }
                }) { Text(stringRes(context, R.string.send)) }
            }
            TextButton(onClick = { messages.clear(); step = 0 }) { Text(stringRes(context, R.string.restart)) }
            OutlinedButton(onClick = {}, enabled = false, modifier = Modifier.fillMaxWidth()) {
                Text(stringRes(context, R.string.subtitle), fontSize = 12.sp)
            }
        }
    }
}

@Composable
private fun MessageBubble(turn: Turn) {
    val mine = turn.sender == "child"
    Box(Modifier.fillMaxWidth(), contentAlignment = if (mine) Alignment.CenterEnd else Alignment.CenterStart) {
        Text(
            turn.text,
            modifier = Modifier
                .widthIn(max = 280.dp)
                .background(if (mine) Purple else Bubble, RoundedCornerShape(14.dp))
                .padding(horizontal = 12.dp, vertical = 8.dp),
            color = if (mine) Color.White else Color(0xFF1A1A1A),
        )
    }
}

/** Hand the message to dcAI Guardian, as an app with the dcAI safety SDK would. */
private fun sendToDcai(context: android.content.Context, turn: Turn, contactKnown: Boolean) {
    val intent = Intent("dev.eziedutech.dcai.guardian.INGEST_MESSAGE").apply {
        setClassName("dev.eziedutech.dcai.guardian", "dev.eziedutech.dcai.guardian.ingest.ChatIngestReceiver")
        putExtra("thread", THREAD)
        putExtra("app", context.packageName)
        putExtra("channel", CHANNEL)
        putExtra("sender", turn.sender)
        putExtra("text", turn.text)
        putExtra("contact_known", contactKnown)
        if (turn.sender == "contact") putExtra("contact_name", "teman_game")
    }
    runCatching { context.sendBroadcast(intent) }
}

private fun dcaiInstalled(context: android.content.Context): Boolean = runCatching {
    context.packageManager.getPackageInfo("dev.eziedutech.dcai.guardian", 0)
    true
}.getOrDefault(false)

private fun stringRes(context: android.content.Context, id: Int): String = context.getString(id)
