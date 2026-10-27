package dev.eziedutech.dcai.samplechat

import android.app.Activity
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.graphics.asImageBitmap
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
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

/** An item in the chat: a text turn, or an image with dcAI's decision once it is known. */
private sealed interface Item {
    val sender: String
}

private data class TextItem(val turn: Turn) : Item {
    override val sender get() = turn.sender
}

private data class ImageItem(
    val id: Int,
    override val sender: String,
    val uri: Uri,
    val shown: Bitmap?,
    val decision: ImageDecision?,
    val checking: Boolean,
    val reviewed: Boolean = false,
) : Item

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
    private lateinit var images: DcaiImageClient

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        images = DcaiImageClient(this).also { it.bind() }
        setContent {
            MaterialTheme {
                Surface(Modifier.fillMaxSize()) { ChatScreen(images) }
            }
        }
    }

    override fun onDestroy() {
        images.unbind()
        super.onDestroy()
    }
}

@Composable
private fun ChatScreen(images: DcaiImageClient) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val messages = remember { mutableStateListOf<Item>() }
    var nextImage by remember { mutableIntStateOf(1) }
    var reviewing by remember { mutableStateOf<Int?>(null) }
    var step by remember { mutableIntStateOf(0) }
    var draft by remember { mutableStateOf("") }
    val listState = rememberLazyListState()
    val linked = remember { dcaiInstalled(context) }

    fun send(turn: Turn, contactKnown: Boolean) {
        messages.add(TextItem(turn))
        sendToDcai(context, turn, contactKnown)
    }

    fun update(id: Int, change: (ImageItem) -> ImageItem) {
        val i = messages.indexOfFirst { it is ImageItem && it.id == id }
        if (i >= 0) messages[i] = change(messages[i] as ImageItem)
    }

    // The image is shown only after dcAI's answer, so a sensitive one is never on screen
    // unblurred. Without dcAI the app shows it as any chat app would.
    fun sendImage(sender: String, uri: Uri) {
        val id = nextImage++
        messages.add(ImageItem(id, sender, uri, shown = null, decision = null, checking = true))
        scope.launch {
            val trigger = if (sender == "child") "dibagikan" else "percakapan"
            val decision = images.check(uri, trigger, THREAD, CHANNEL, sender)
            val shown = withContext(Dispatchers.Default) { loadBitmap(context, uri)?.let { Blur.apply(it, decision) } }
            update(id) { it.copy(shown = shown, decision = decision, checking = false) }
        }
    }

    val review = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        val id = reviewing ?: return@rememberLauncherForActivityResult
        reviewing = null
        if (result.resultCode == Activity.RESULT_OK) {
            scope.launch {
                val item = messages.filterIsInstance<ImageItem>().firstOrNull { it.id == id } ?: return@launch
                val shown = withContext(Dispatchers.Default) { loadBitmap(context, item.uri) }
                update(id) { it.copy(shown = shown, reviewed = true) }
            }
        }
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
            items(messages) { item ->
                when (item) {
                    is TextItem -> MessageBubble(item.turn)
                    is ImageItem -> ImageBubble(item, onReview = {
                        val decision = item.decision
                        if (decision != null) {
                            reviewing = item.id
                            runCatching { review.launch(images.reviewIntent(item.uri, decision)) }
                        }
                    })
                }
            }
        }

        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            if (step < SCENARIO.size) {
                Button(onClick = { send(SCENARIO[step], contactKnown = false); step++ }, modifier = Modifier.fillMaxWidth()) {
                    Text(stringRes(context, R.string.play_next))
                }
            } else {
                Text(stringRes(context, R.string.done), color = Purple, fontWeight = FontWeight.Bold)
            }
            if (step >= SCENARIO.size) {
                OutlinedButton(onClick = { sendImage("contact", SampleImages.invitation(context)) }, modifier = Modifier.fillMaxWidth()) {
                    Text(stringRes(context, R.string.contact_image))
                }
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = { sendImage("child", SampleImages.studentCard(context)) }, modifier = Modifier.weight(1f)) {
                    Text(stringRes(context, R.string.share_card), fontSize = 12.sp)
                }
                OutlinedButton(onClick = { sendImage("child", SampleImages.landscape(context)) }, modifier = Modifier.weight(1f)) {
                    Text(stringRes(context, R.string.share_landscape), fontSize = 12.sp)
                }
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
private fun ImageBubble(item: ImageItem, onReview: () -> Unit) {
    val context = LocalContext.current
    val mine = item.sender == "child"
    val textColor = if (mine) Color.White else Color(0xFF1A1A1A)
    Box(Modifier.fillMaxWidth(), contentAlignment = if (mine) Alignment.CenterEnd else Alignment.CenterStart) {
        Column(
            Modifier.widthIn(max = 280.dp).background(if (mine) Purple else Bubble, RoundedCornerShape(14.dp)).padding(8.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            val shown = item.shown
            if (item.checking || shown == null) {
                Text(stringRes(context, R.string.checking), color = textColor, fontSize = 13.sp)
            } else {
                Image(shown.asImageBitmap(), contentDescription = null, modifier = Modifier.fillMaxWidth())
                val decision = item.decision
                if (item.reviewed) {
                    Text(stringRes(context, R.string.reviewed), color = textColor, fontSize = 12.sp)
                } else if (decision != null && decision.blurred) {
                    val note = when {
                        decision.blurAll -> R.string.blurred_all
                        mine -> R.string.blurred_shared
                        else -> R.string.blurred_private
                    }
                    Text(stringRes(context, note), color = textColor, fontSize = 12.sp)
                    TextButton(onClick = onReview) { Text(stringRes(context, R.string.ask_review), color = textColor) }
                }
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

private fun loadBitmap(context: android.content.Context, uri: Uri): Bitmap? =
    runCatching { context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it) } }.getOrNull()

private fun stringRes(context: android.content.Context, id: Int): String = context.getString(id)
