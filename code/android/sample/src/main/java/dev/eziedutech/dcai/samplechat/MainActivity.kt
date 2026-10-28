package dev.eziedutech.dcai.samplechat

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.Send
import androidx.compose.material.icons.rounded.AttachFile
import androidx.compose.material.icons.rounded.Call
import androidx.compose.material.icons.rounded.CameraAlt
import androidx.compose.material.icons.rounded.DoneAll
import androidx.compose.material.icons.rounded.Edit
import androidx.compose.material.icons.rounded.MoreVert
import androidx.compose.material.icons.rounded.Search
import androidx.compose.material.icons.rounded.Shield
import androidx.compose.material.icons.rounded.SentimentSatisfied
import androidx.compose.material.icons.rounded.Videocam
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledIconButton
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TextField
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.input.key.Key
import androidx.compose.ui.input.key.KeyEventType
import androidx.compose.ui.input.key.isShiftPressed
import androidx.compose.ui.input.key.key
import androidx.compose.ui.input.key.onPreviewKeyEvent
import androidx.compose.ui.input.key.type
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.LocalTime
import java.time.format.DateTimeFormatter

/** One message of a chat. `from` names the sender in a group. Synthetic data only. */
private data class Turn(val sender: String, val text: String, val from: String? = null)

/** An item in a chat: a text turn, or an image with dcAI's decision once it is known. */
private sealed interface Item {
    val sender: String
    val time: String
}

private data class TextItem(val turn: Turn, override val time: String) : Item {
    override val sender get() = turn.sender
}

private data class ImageItem(
    val id: Int,
    override val sender: String,
    override val time: String,
    val uri: Uri,
    val shown: Bitmap?,
    val decision: ImageDecision?,
    val checking: Boolean,
    val reviewed: Boolean = false,
) : Item

/**
 * A chat in the list. `script` is what the contact says next, one turn after each thing the
 * child sends; the first turn has arrived when the app opens. Every name and message is
 * invented for the demo.
 */
private data class Contact(
    val id: String,
    val name: String,
    val handle: String,
    val color: Color,
    val known: Boolean,
    val group: Boolean = false,
    val history: List<Pair<Turn, String>> = emptyList(),
    val script: List<Turn> = emptyList(),
)

// A short staged approach a contact might use. Synthetic, for testing dcAI.
private val NEW_FRIEND = Contact(
    id = "newfriend", name = "Kak Bima", handle = "teman_game", color = Color(0xFFEA580C), known = false,
    script = listOf(
        Turn("contact", "halo, kamu jago banget mainnya, beda dari yang lain"),
        Turn("contact", "main bareng yuk tiap hari, nanti aku ajarin trik"),
        Turn("contact", "aku kasih skin gratis, tapi jangan bilang siapa-siapa ya"),
        Turn("contact", "kirim foto kamu dong, terus kita lanjut ngobrol di aplikasi lain"),
    ),
)

private val CONTACTS = listOf(
    NEW_FRIEND,
    Contact(
        id = "ipa8b", name = "Kelompok IPA 8B", handle = "kelompok_ipa", color = Color(0xFF0891B2), known = true, group = true,
        history = listOf(
            Turn("contact", "besok bawa karton buat poster ya", from = "Dinda") to "19.02",
            Turn("child", "siap, aku bawa spidol juga") to "19.05",
            Turn("contact", "aku bawa lem sama gunting", from = "Raka") to "19.11",
        ),
    ),
    Contact(
        id = "mama", name = "Mama", handle = "mama", color = Color(0xFFDB2777), known = true,
        history = listOf(
            Turn("contact", "Nak, jangan lupa makan ya") to "12.30",
            Turn("child", "iya Ma, udah kok") to "12.41",
        ),
    ),
    Contact(
        id = "dinda", name = "Dinda", handle = "dinda", color = Color(0xFF16A34A), known = true,
        history = listOf(
            Turn("contact", "nanti malam mabar?") to "Kemarin",
            Turn("child", "boleh, abis belajar ya") to "Kemarin",
        ),
    ),
)

private const val CHANNEL = "game_chat"

private val Purple = Color(0xFF4C1D95)
private val PurpleSoft = Color(0xFFE9E0FB)
private val Wallpaper = Color(0xFFF4F1F8)
private val Ink = Color(0xFF1A1A1A)
private val Muted = Color(0xFF6B6578)

private val clock = DateTimeFormatter.ofPattern("HH.mm")
private fun now(): String = LocalTime.now().format(clock)

/** The state of one chat; kept while the app runs so going back to the list loses nothing. */
private class ChatState(val contact: Contact, run: Long) {
    // Each app start is a new thread for dcAI, so repeated demo runs stay apart.
    var thread = "messengerz-${contact.id}-$run"
    val messages = mutableStateListOf<Item>().apply { contact.history.forEach { (t, time) -> add(TextItem(t, time)) } }
    var step by mutableIntStateOf(0)
    var typing by mutableStateOf(false)
    var unread by mutableIntStateOf(0)
    var invitationSent by mutableStateOf(false)
}

/**
 * Demo commands, so a recorded run can be driven from a computer without tapping at
 * coordinates: `adb shell am start -n dev.eziedutech.dcai.samplechat/.MainActivity --es demo card`.
 * open, back, focus, card, landscape, next, image, restart.
 */
private val demo = mutableStateOf<String?>(null)

class MainActivity : ComponentActivity() {
    private lateinit var images: DcaiImageClient

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        intent.getStringExtra("demo")?.let { demo.value = it }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge(statusBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT))
        images = DcaiImageClient(this).also { it.bind() }
        intent?.getStringExtra("demo")?.let { demo.value = it }
        setContent {
            MaterialTheme {
                Surface(Modifier.fillMaxSize(), color = Color.White) { App(images) }
            }
        }
    }

    override fun onDestroy() {
        images.unbind()
        super.onDestroy()
    }
}

@Composable
private fun App(images: DcaiImageClient) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val run = remember { System.currentTimeMillis() / 1000 }
    val chats = remember { CONTACTS.associate { it.id to ChatState(it, run) } }
    val linked = remember { dcaiInstalled(context) }
    var open by remember { mutableStateOf<String?>(null) }

    // The new friend's first message has arrived when the app opens.
    LaunchedEffect(Unit) {
        val chat = chats.getValue(NEW_FRIEND.id)
        if (chat.step == 0) deliver(context, chat)
        chat.unread = 1
    }

    val command = demo.value
    LaunchedEffect(command) {
        when (command) {
            "open" -> { chats.getValue(NEW_FRIEND.id).unread = 0; open = NEW_FRIEND.id }
            "back" -> open = null
        }
        if (command == "open" || command == "back") demo.value = null
    }

    val current = open?.let(chats::get)
    if (current == null) {
        ChatList(chats.values.toList(), linked) { id -> chats.getValue(id).unread = 0; open = id }
    } else {
        BackHandler { open = null }
        ChatScreen(current, images, scope, onBack = { open = null })
    }
}

/** The contact's next scripted turn reaches the chat and dcAI. */
private fun deliver(context: Context, chat: ChatState) {
    val turn = chat.contact.script.getOrNull(chat.step) ?: return
    chat.step++
    chat.messages.add(TextItem(turn, now()))
    sendToDcai(context, chat, turn)
}

/** After the child sends something, the contact types for a moment and answers. */
private fun answerLater(context: Context, chat: ChatState, scope: CoroutineScope, sendImage: (String, Uri) -> Unit) {
    if (chat.typing) return
    val hasTurn = chat.step < chat.contact.script.size
    val hasImage = !hasTurn && chat.contact.script.isNotEmpty() && !chat.invitationSent
    if (!hasTurn && !hasImage) return
    scope.launch {
        delay(900)
        chat.typing = true
        delay(1800)
        chat.typing = false
        if (hasTurn) deliver(context, chat) else {
            chat.invitationSent = true
            sendImage("contact", SampleImages.invitation(context))
        }
    }
}

@Composable
private fun ChatList(chats: List<ChatState>, linked: Boolean, onOpen: (String) -> Unit) {
    Box(Modifier.fillMaxSize()) {
        Column(Modifier.fillMaxSize()) {
            Column(Modifier.fillMaxWidth().background(Purple).statusBarsPadding().padding(start = 20.dp, end = 8.dp, top = 8.dp, bottom = 12.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(stringResource(R.string.app_name), color = Color.White, fontWeight = FontWeight.Bold, fontSize = 22.sp, modifier = Modifier.weight(1f))
                    IconButton(onClick = {}) { Icon(Icons.Rounded.CameraAlt, null, tint = Color.White) }
                    IconButton(onClick = {}) { Icon(Icons.Rounded.Search, null, tint = Color.White) }
                    IconButton(onClick = {}) { Icon(Icons.Rounded.MoreVert, null, tint = Color.White) }
                }
                Row(
                    Modifier.padding(top = 4.dp).background(Color.White.copy(alpha = 0.16f), RoundedCornerShape(50)).padding(horizontal = 10.dp, vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(Icons.Rounded.Shield, null, tint = Color.White, modifier = Modifier.size(14.dp))
                    Spacer(Modifier.width(6.dp))
                    Text(stringResource(if (linked) R.string.linked else R.string.not_linked), color = Color.White, fontSize = 12.sp)
                }
            }
            LazyColumn(Modifier.weight(1f).fillMaxWidth()) {
                items(chats, key = { it.contact.id }) { chat -> ChatRow(chat) { onOpen(chat.contact.id) } }
                item {
                    Text(
                        stringResource(R.string.synthetic_note), color = Muted, fontSize = 12.sp,
                        modifier = Modifier.fillMaxWidth().padding(24.dp),
                    )
                }
            }
        }
        FloatingActionButton(
            onClick = {}, containerColor = Purple, contentColor = Color.White,
            modifier = Modifier.align(Alignment.BottomEnd).navigationBarsPadding().padding(20.dp),
        ) { Icon(Icons.Rounded.Edit, null) }
    }
}

@Composable
private fun ChatRow(chat: ChatState, onClick: () -> Unit) {
    val last = chat.messages.lastOrNull()
    val preview = when (last) {
        is TextItem -> (if (last.sender == "child") stringResource(R.string.you_prefix) else last.turn.from?.let { "$it: " } ?: "") + last.turn.text
        is ImageItem -> stringResource(R.string.photo)
        null -> ""
    }
    Row(
        Modifier.fillMaxWidth().clickable(onClick = onClick).padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Avatar(chat.contact, 52)
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(chat.contact.name, fontWeight = FontWeight.SemiBold, fontSize = 16.sp, color = Ink, modifier = Modifier.weight(1f), maxLines = 1)
                Text(last?.time ?: "", fontSize = 12.sp, color = if (chat.unread > 0) Purple else Muted)
            }
            Spacer(Modifier.height(3.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    if (chat.typing) stringResource(R.string.typing) else preview,
                    fontSize = 14.sp, color = if (chat.typing) Purple else Muted,
                    maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.weight(1f),
                )
                if (chat.unread > 0) {
                    Box(Modifier.padding(start = 8.dp).size(22.dp).background(Purple, CircleShape), contentAlignment = Alignment.Center) {
                        Text("${chat.unread}", color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
}

@Composable
private fun Avatar(contact: Contact, size: Int) {
    val initials = contact.name.split(" ").filter { it.isNotBlank() }.take(2).joinToString("") { it.first().uppercase() }
    Box(Modifier.size(size.dp).background(contact.color, CircleShape), contentAlignment = Alignment.Center) {
        Text(initials, color = Color.White, fontWeight = FontWeight.Bold, fontSize = (size / 2.6).sp)
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ChatScreen(chat: ChatState, images: DcaiImageClient, scope: CoroutineScope, onBack: () -> Unit) {
    val context = LocalContext.current
    var nextImage by remember { mutableIntStateOf(1) }
    var reviewing by remember { mutableStateOf<Int?>(null) }
    var draft by remember { mutableStateOf("") }
    var menu by remember { mutableStateOf(false) }
    var gallery by remember { mutableStateOf(false) }
    val listState = rememberLazyListState()
    val messages = chat.messages
    val focus = LocalFocusManager.current
    val field = remember { FocusRequester() }

    fun update(id: Int, change: (ImageItem) -> ImageItem) {
        val i = messages.indexOfFirst { it is ImageItem && it.id == id }
        if (i >= 0) messages[i] = change(messages[i] as ImageItem)
    }

    // The image is shown only after dcAI's answer, so a sensitive one is never on screen
    // unblurred. Without dcAI the app shows it as any chat app would.
    fun sendImage(sender: String, uri: Uri) {
        val id = nextImage++
        messages.add(ImageItem(id, sender, now(), uri, shown = null, decision = null, checking = true))
        scope.launch {
            val trigger = if (sender == "child") "dibagikan" else "percakapan"
            val decision = images.check(uri, trigger, chat.thread, CHANNEL, sender)
            val shown = withContext(Dispatchers.Default) { loadBitmap(context, uri)?.let { Blur.apply(it, decision) } }
            update(id) { it.copy(shown = shown, decision = decision, checking = false) }
        }
    }

    fun childSends(text: String) {
        val turn = Turn("child", text)
        messages.add(TextItem(turn, now()))
        sendToDcai(context, chat, turn)
        answerLater(context, chat, scope, ::sendImage)
    }

    fun send() {
        val text = draft.trim()
        if (text.isNotEmpty()) {
            childSends(text)
            draft = ""
        }
    }

    // A new thread for dcAI, so a repeated run starts from a clean conversation.
    fun restart() {
        messages.clear()
        chat.contact.history.forEach { (t, time) -> messages.add(TextItem(t, time)) }
        chat.step = 0
        chat.invitationSent = false
        chat.thread = "messengerz-${chat.contact.id}-${System.currentTimeMillis() / 1000}"
        deliver(context, chat)
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

    // Also when an image finishes checking, since its bubble grows.
    val ready = messages.count { it is ImageItem && !it.checking }
    val command = demo.value
    LaunchedEffect(command) {
        val done = when (command) {
            "card" -> { sendImage("child", SampleImages.studentCard(context)); answerLater(context, chat, scope, ::sendImage); true }
            "landscape" -> { sendImage("child", SampleImages.landscape(context)); true }
            "next" -> { deliver(context, chat); true }
            "image" -> { chat.invitationSent = true; sendImage("contact", SampleImages.invitation(context)); true }
            "restart" -> { restart(); true }
            "focus" -> { runCatching { field.requestFocus() }; true }
            else -> false
        }
        if (done) demo.value = null
    }

    LaunchedEffect(messages.size, chat.typing, ready) {
        // Day chip, messages, typing dots, bottom spacer.
        listState.animateScrollToItem(messages.size + 1 + if (chat.typing) 1 else 0)
    }

    Column(Modifier.fillMaxSize().background(Wallpaper).imePadding()) {
        Row(
            Modifier.fillMaxWidth().background(Purple).statusBarsPadding().padding(horizontal = 4.dp, vertical = 6.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Rounded.ArrowBack, null, tint = Color.White) }
            Avatar(chat.contact, 40)
            Spacer(Modifier.width(10.dp))
            Column(Modifier.weight(1f)) {
                Text(chat.contact.name, color = Color.White, fontWeight = FontWeight.SemiBold, fontSize = 17.sp, maxLines = 1)
                val status = when {
                    chat.typing -> stringResource(R.string.typing)
                    chat.contact.group -> stringResource(R.string.group_members)
                    else -> stringResource(R.string.online)
                }
                Text(status, color = Color.White.copy(alpha = 0.85f), fontSize = 12.sp, maxLines = 1)
            }
            IconButton(onClick = {}) { Icon(Icons.Rounded.Videocam, null, tint = Color.White) }
            IconButton(onClick = {}) { Icon(Icons.Rounded.Call, null, tint = Color.White) }
            Box {
                IconButton(onClick = { menu = true }) { Icon(Icons.Rounded.MoreVert, null, tint = Color.White) }
                DemoMenu(menu, chat, onDismiss = { menu = false }, onNext = { deliver(context, chat) }, onImage = {
                    chat.invitationSent = true
                    sendImage("contact", SampleImages.invitation(context))
                }, onRestart = ::restart)
            }
        }

        LazyColumn(
            state = listState,
            modifier = Modifier.weight(1f).fillMaxWidth().padding(horizontal = 10.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            item { DayChip() }
            items(messages) { item ->
                when (item) {
                    is TextItem -> MessageBubble(item, chat.contact.group)
                    is ImageItem -> ImageBubble(item, onReview = {
                        val decision = item.decision
                        if (decision != null) {
                            reviewing = item.id
                            runCatching { review.launch(images.reviewIntent(item.uri, decision)) }
                        }
                    })
                }
            }
            if (chat.typing) item { TypingBubble() }
            item { Spacer(Modifier.height(6.dp)) }
        }

        Row(
            Modifier.fillMaxWidth().navigationBarsPadding().padding(horizontal = 8.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            TextField(
                value = draft, onValueChange = { draft = it },
                placeholder = { Text(stringResource(R.string.type_hint)) },
                leadingIcon = { Icon(Icons.Rounded.SentimentSatisfied, null, tint = Muted) },
                trailingIcon = {
                    IconButton(onClick = { focus.clearFocus(); gallery = true }) { Icon(Icons.Rounded.AttachFile, stringResource(R.string.attach), tint = Muted) }
                },
                shape = RoundedCornerShape(28.dp),
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = Color.White, unfocusedContainerColor = Color.White,
                    focusedIndicatorColor = Color.Transparent, unfocusedIndicatorColor = Color.Transparent,
                ),
                maxLines = 4,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                keyboardActions = KeyboardActions(onSend = { send() }),
                // A hardware Enter sends too, as on a computer keyboard.
                modifier = Modifier.weight(1f).focusRequester(field).onPreviewKeyEvent {
                    if (it.key == Key.Enter && !it.isShiftPressed) {
                        if (it.type == KeyEventType.KeyDown) send()
                        true
                    } else false
                },
            )
            Spacer(Modifier.width(6.dp))
            FilledIconButton(
                onClick = ::send,
                colors = IconButtonDefaults.filledIconButtonColors(containerColor = Purple, contentColor = Color.White),
                modifier = Modifier.size(52.dp),
            ) { Icon(Icons.AutoMirrored.Rounded.Send, stringResource(R.string.send)) }
        }
    }

    if (gallery) {
        ModalBottomSheet(onDismissRequest = { gallery = false }, containerColor = Color.White) {
            Gallery { uri ->
                gallery = false
                sendImage("child", uri)
                answerLater(context, chat, scope, ::sendImage)
            }
        }
    }
}

@Composable
private fun DemoMenu(open: Boolean, chat: ChatState, onDismiss: () -> Unit, onNext: () -> Unit, onImage: () -> Unit, onRestart: () -> Unit) {
    DropdownMenu(expanded = open, onDismissRequest = onDismiss) {
        if (chat.contact.script.isNotEmpty()) {
            DropdownMenuItem(
                text = { Text(stringResource(R.string.demo_next)) },
                enabled = chat.step < chat.contact.script.size,
                onClick = { onDismiss(); onNext() },
            )
            DropdownMenuItem(text = { Text(stringResource(R.string.demo_image)) }, onClick = { onDismiss(); onImage() })
            HorizontalDivider()
            DropdownMenuItem(text = { Text(stringResource(R.string.restart)) }, onClick = { onDismiss(); onRestart() })
        } else {
            DropdownMenuItem(text = { Text(stringResource(R.string.restart)) }, onClick = { onDismiss(); onRestart() })
        }
    }
}

/** The phone's gallery, as far as this demo needs: two synthetic pictures. */
@Composable
private fun Gallery(onPick: (Uri) -> Unit) {
    val context = LocalContext.current
    val picks = produceState<List<Triple<Int, Uri, Bitmap?>>>(emptyList()) {
        value = withContext(Dispatchers.IO) {
            listOf(
                R.string.share_card to SampleImages.studentCard(context),
                R.string.share_landscape to SampleImages.landscape(context),
            ).map { (label, uri) -> Triple(label, uri, loadBitmap(context, uri)) }
        }
    }.value
    Column(Modifier.fillMaxWidth().navigationBarsPadding().padding(horizontal = 20.dp).padding(bottom = 24.dp)) {
        Text(stringResource(R.string.gallery), fontWeight = FontWeight.SemiBold, fontSize = 18.sp, color = Ink)
        Spacer(Modifier.height(14.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            picks.forEach { (label, uri, bitmap) ->
                Column(Modifier.weight(1f).clip(RoundedCornerShape(14.dp)).clickable { onPick(uri) }) {
                    if (bitmap != null) {
                        Image(
                            bitmap.asImageBitmap(), stringResource(label), contentScale = ContentScale.Crop,
                            modifier = Modifier.fillMaxWidth().height(110.dp).clip(RoundedCornerShape(14.dp)),
                        )
                    }
                    Text(stringResource(label), fontSize = 13.sp, color = Muted, modifier = Modifier.padding(top = 6.dp))
                }
            }
        }
    }
}

@Composable
private fun DayChip() {
    Column(Modifier.fillMaxWidth().padding(vertical = 10.dp), horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            stringResource(R.string.today), fontSize = 12.sp, color = Muted,
            modifier = Modifier.background(Color.White, RoundedCornerShape(8.dp)).padding(horizontal = 10.dp, vertical = 4.dp),
        )
    }
}

private fun bubbleShape(mine: Boolean) = RoundedCornerShape(
    topStart = 16.dp, topEnd = 16.dp,
    bottomStart = if (mine) 16.dp else 4.dp, bottomEnd = if (mine) 4.dp else 16.dp,
)

@Composable
private fun Bubble(mine: Boolean, content: @Composable () -> Unit) {
    Box(Modifier.fillMaxWidth().padding(vertical = 1.dp), contentAlignment = if (mine) Alignment.CenterEnd else Alignment.CenterStart) {
        Box(
            Modifier.widthIn(max = 290.dp).background(if (mine) PurpleSoft else Color.White, bubbleShape(mine)).padding(horizontal = 10.dp, vertical = 6.dp),
        ) { content() }
    }
}

@Composable
private fun Stamp(time: String, mine: Boolean, modifier: Modifier = Modifier) {
    Row(modifier, verticalAlignment = Alignment.CenterVertically) {
        Text(time, fontSize = 11.sp, color = Muted)
        if (mine) {
            Spacer(Modifier.width(3.dp))
            Icon(Icons.Rounded.DoneAll, null, tint = Purple, modifier = Modifier.size(15.dp))
        }
    }
}

@Composable
private fun MessageBubble(item: TextItem, group: Boolean) {
    val mine = item.sender == "child"
    Bubble(mine) {
        Column {
            val from = item.turn.from
            if (group && !mine && from != null) Text(from, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = Color(0xFF0891B2))
            Text(item.turn.text, color = Ink, fontSize = 15.sp)
            Stamp(item.time, mine, Modifier.align(Alignment.End))
        }
    }
}

@Composable
private fun ImageBubble(item: ImageItem, onReview: () -> Unit) {
    val mine = item.sender == "child"
    Bubble(mine) {
        Column(Modifier.width(250.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            val shown = item.shown
            if (item.checking || shown == null) {
                Row(Modifier.fillMaxWidth().height(140.dp).background(Color(0x14000000), RoundedCornerShape(12.dp)), horizontalArrangement = Arrangement.Center, verticalAlignment = Alignment.CenterVertically) {
                    CircularProgressIndicator(Modifier.size(20.dp), color = Purple, strokeWidth = 2.dp)
                    Spacer(Modifier.width(10.dp))
                    Text(stringResource(R.string.checking), color = Muted, fontSize = 13.sp)
                }
            } else {
                Image(shown.asImageBitmap(), contentDescription = null, modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp)))
                val decision = item.decision
                if (item.reviewed) {
                    Text(stringResource(R.string.reviewed), color = Ink, fontSize = 12.sp)
                } else if (decision != null && decision.blurred) {
                    val note = when {
                        decision.blurAll -> R.string.blurred_all
                        mine -> R.string.blurred_shared
                        else -> R.string.blurred_private
                    }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Rounded.Shield, null, tint = Purple, modifier = Modifier.size(14.dp))
                        Spacer(Modifier.width(6.dp))
                        Text(stringResource(note), color = Ink, fontSize = 12.sp)
                    }
                    TextButton(onClick = onReview) { Text(stringResource(R.string.ask_review), color = Purple) }
                }
            }
            Stamp(item.time, mine, Modifier.align(Alignment.End))
        }
    }
}

@Composable
private fun TypingBubble() {
    val pulse = rememberInfiniteTransition(label = "typing")
    Bubble(mine = false) {
        Row(Modifier.padding(vertical = 6.dp, horizontal = 4.dp), horizontalArrangement = Arrangement.spacedBy(5.dp)) {
            repeat(3) { i ->
                val a by pulse.animateFloat(
                    0.25f, 1f, infiniteRepeatable(tween(500, delayMillis = i * 160), RepeatMode.Reverse), label = "dot$i",
                )
                Box(Modifier.size(8.dp).alpha(a).background(Muted, CircleShape))
            }
        }
    }
}

/** Hand the message to dcAI Guardian, as an app with the dcAI safety SDK would. */
private fun sendToDcai(context: Context, chat: ChatState, turn: Turn) {
    val intent = Intent("dev.eziedutech.dcai.guardian.INGEST_MESSAGE").apply {
        setClassName("dev.eziedutech.dcai.guardian", "dev.eziedutech.dcai.guardian.ingest.ChatIngestReceiver")
        putExtra("thread", chat.thread)
        putExtra("app", context.packageName)
        putExtra("channel", CHANNEL)
        putExtra("sender", turn.sender)
        putExtra("text", turn.text)
        putExtra("contact_known", chat.contact.known)
        if (turn.sender == "contact") putExtra("contact_name", chat.contact.handle)
    }
    runCatching { context.sendBroadcast(intent) }
}

private fun dcaiInstalled(context: Context): Boolean = runCatching {
    context.packageManager.getPackageInfo(GUARDIAN, 0)
    true
}.getOrDefault(false)

private fun loadBitmap(context: Context, uri: Uri): Bitmap? =
    runCatching { context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it) } }.getOrNull()
