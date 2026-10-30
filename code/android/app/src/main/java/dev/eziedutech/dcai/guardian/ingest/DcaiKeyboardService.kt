package dev.eziedutech.dcai.guardian.ingest

import android.annotation.SuppressLint
import android.inputmethodservice.InputMethodService
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.HapticFeedbackConstants
import android.view.MotionEvent
import android.view.View
import android.view.inputmethod.EditorInfo
import android.widget.Button
import android.widget.LinearLayout
import dev.eziedutech.dcai.guardian.ServiceLocator
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

/**
 * The dcAI keyboard. A small but usable soft keyboard that also checks the text the child
 * types. It only ever sees the child's own typing in the current app, never the other
 * person's messages. When the child sends, the buffer is masked on the phone and submitted
 * for assessment, the same path the sample chat app uses. Sending is the keyboard's own
 * action key, or the app's send button: chat apps empty the field after sending, and an
 * emptied field with typed text in the buffer counts as sent.
 *
 * Letters with a three-state Shift (one-shot, caps lock, off), a numbers-and-symbols layer,
 * an emoji layer, light haptics, and long-press (top row to digits, period to comma, Del to
 * repeat), so a child can use it as their everyday keyboard. The child knows it is dcAI: it
 * is named "dcAI" in the keyboard picker and the guardian notification stays visible.
 */
class DcaiKeyboardService : InputMethodService() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private val buffer = StringBuilder()
    private val handler = Handler(Looper.getMainLooper())
    private var repeatDelete: Runnable? = null

    private enum class Caps { OFF, SHIFT, LOCK }
    private enum class Layer { LETTERS, SYMBOLS, EMOJI }

    private var caps = Caps.OFF
    private var layer = Layer.LETTERS
    private lateinit var root: LinearLayout

    private val letterRows = listOf("qwertyuiop", "asdfghjkl", "zxcvbnm")
    private val topDigits = "1234567890" // long-press on the top letter row types these
    private val symbolRows = listOf("1234567890", "@#\$_&-+()/", "*\"':;!?")
    private val emojis = listOf(
        "😀", "😁", "😂", "🤣", "😊", "😍", "😘", "😎",
        "🤔", "😅", "😭", "😡", "😴", "🥳", "😇", "🤝",
        "👍", "👎", "👌", "🙏", "👏", "💪", "🙌", "🤗",
        "🎉", "❤️", "🔥", "✨", "⭐", "✅", "❌", "❓",
    )

    override fun onCreateInputView(): View {
        root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(8, 8, 8, 24)
        }
        render()
        return root
    }

    /** Rebuild the keys for the current layer and Shift state. */
    private fun render() {
        root.removeAllViews()
        when (layer) {
            Layer.LETTERS -> renderLetters()
            Layer.SYMBOLS -> renderSymbols()
            Layer.EMOJI -> renderEmoji()
        }
    }

    private fun renderLetters() {
        letterRows.forEachIndexed { i, chars ->
            val line = row()
            if (i == letterRows.lastIndex) {
                line.addView(key(shiftLabel()) { onShift() }, weight(1.5f))
                chars.forEach { ch -> line.addView(letterKey(ch.toString()), weight()) }
                line.addView(deleteKey(), weight(1.5f))
            } else {
                chars.forEachIndexed { j, ch ->
                    val long = if (i == 0) topDigits.getOrNull(j)?.toString() else null
                    line.addView(letterKey(ch.toString(), long), weight())
                }
            }
            root.addView(line)
        }
        val bottom = row()
        bottom.addView(key("?123") { setLayer(Layer.SYMBOLS) }, weight(1.5f))
        bottom.addView(key("😊") { setLayer(Layer.EMOJI) }, weight(1.2f))
        bottom.addView(key("space") { type(" ") }, weight(4f))
        bottom.addView(key(".") { type(".") }.withLongPress(",") { type(",") }, weight())
        bottom.addView(sendKey(), weight(2f))
        root.addView(bottom)
    }

    private fun renderSymbols() {
        symbolRows.forEachIndexed { i, chars ->
            val line = row()
            chars.forEach { ch -> line.addView(key(ch.toString()) { type(ch.toString()) }, weight()) }
            if (i == symbolRows.lastIndex) line.addView(deleteKey(), weight(1.5f))
            root.addView(line)
        }
        val bottom = row()
        bottom.addView(key("ABC") { setLayer(Layer.LETTERS) }, weight(1.5f))
        bottom.addView(key("😊") { setLayer(Layer.EMOJI) }, weight(1.2f))
        bottom.addView(key("space") { type(" ") }, weight(4f))
        bottom.addView(key(",") { type(",") }, weight())
        bottom.addView(sendKey(), weight(2f))
        root.addView(bottom)
    }

    private fun renderEmoji() {
        emojis.chunked(8).forEach { group ->
            val line = row()
            group.forEach { e -> line.addView(key(e) { type(e) }, weight()) }
            root.addView(line)
        }
        val bottom = row()
        bottom.addView(key("ABC") { setLayer(Layer.LETTERS) }, weight(1.5f))
        bottom.addView(key("space") { type(" ") }, weight(5f))
        bottom.addView(deleteKey(), weight(1.5f))
        bottom.addView(sendKey(), weight(2f))
        root.addView(bottom)
    }

    private fun row() = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }

    private fun shiftLabel() = if (caps == Caps.LOCK) "⇪" else "⇧"

    private fun letterKey(ch: String, longText: String? = null): Button {
        val shown = if (layer == Layer.LETTERS && caps != Caps.OFF) ch.uppercase() else ch
        val b = key(shown) { type(shown) }
        return if (longText != null) b.withLongPress(longText) { type(longText) } else b
    }

    private fun key(label: String, onClick: () -> Unit) = Button(this).apply {
        text = label
        isAllCaps = false
        setOnClickListener { v ->
            v.performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP)
            onClick()
        }
    }

    private fun Button.withLongPress(hint: String, onLong: () -> Unit): Button = apply {
        setOnLongClickListener {
            performHapticFeedback(HapticFeedbackConstants.LONG_PRESS)
            onLong()
            true
        }
    }

    private fun sendKey() =
        key(getString(dev.eziedutech.dcai.guardian.R.string.keyboard_check)) { send() }

    /** Del that repeats while held. */
    @SuppressLint("ClickableViewAccessibility")
    private fun deleteKey() = Button(this).apply {
        text = "⌫"
        isAllCaps = false
        setOnTouchListener { v, e ->
            when (e.actionMasked) {
                MotionEvent.ACTION_DOWN -> {
                    v.performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP)
                    backspace()
                    val r = object : Runnable {
                        override fun run() {
                            backspace()
                            handler.postDelayed(this, 55)
                        }
                    }
                    repeatDelete = r
                    handler.postDelayed(r, 350)
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    stopRepeatDelete()
                    v.performClick()
                    true
                }
                else -> false
            }
        }
    }

    private fun stopRepeatDelete() {
        repeatDelete?.let { handler.removeCallbacks(it) }
        repeatDelete = null
    }

    private fun weight(w: Float = 1f) =
        LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, w).apply { gravity = Gravity.CENTER }

    private fun onShift() {
        caps = when (caps) {
            Caps.OFF -> Caps.SHIFT
            Caps.SHIFT -> Caps.LOCK
            Caps.LOCK -> Caps.OFF
        }
        render()
    }

    private fun setLayer(next: Layer) {
        layer = next
        caps = Caps.OFF
        render()
    }

    private fun type(text: String) {
        currentInputConnection?.commitText(text, 1)
        buffer.append(text)
        // A one-shot Shift drops back to lowercase after a letter is typed.
        if (caps == Caps.SHIFT && text.firstOrNull()?.isLetter() == true) {
            caps = Caps.OFF
            render()
        }
    }

    private fun backspace() {
        currentInputConnection?.deleteSurroundingText(1, 0)
        if (buffer.isNotEmpty()) buffer.deleteCharAt(buffer.length - 1)
    }

    /** Commit a newline to the field and hand the typed text to dcAI. */
    private fun send() {
        currentInputConnection?.commitText("\n", 1)
        submitBuffer()
    }

    /** The app emptied the field (its send button): what was typed has been sent. */
    override fun onUpdateSelection(
        oldSelStart: Int, oldSelEnd: Int, newSelStart: Int, newSelEnd: Int, candidatesStart: Int, candidatesEnd: Int,
    ) {
        super.onUpdateSelection(oldSelStart, oldSelEnd, newSelStart, newSelEnd, candidatesStart, candidatesEnd)
        if (buffer.isEmpty() || newSelStart != 0 || newSelEnd != 0) return
        val ic = currentInputConnection ?: return
        val empty = ic.getTextBeforeCursor(1, 0).isNullOrEmpty() && ic.getTextAfterCursor(1, 0).isNullOrEmpty()
        if (empty) submitBuffer()
    }

    private fun submitBuffer() {
        val text = buffer.toString().trim()
        buffer.clear()
        if (text.isEmpty()) return
        val ingest = ServiceLocator.ingest(this) ?: return
        val targetApp = currentInputEditorInfo?.packageName ?: "unknown.app"
        // The chat whose messages arrived last in this app, when there is one: the reply
        // and the messages it answers are one conversation.
        val thread = RecentThreads.current(targetApp) ?: targetApp
        scope.launch {
            runCatching {
                ingest.submit(
                    threadId = thread,
                    appPackage = targetApp,
                    channel = "dm",
                    contactKnown = false,
                    sender = "child",
                    rawText = text,
                )
            }
        }
    }

    override fun onStartInput(attribute: EditorInfo?, restarting: Boolean) {
        super.onStartInput(attribute, restarting)
        buffer.clear()
        caps = Caps.OFF
        layer = Layer.LETTERS
        stopRepeatDelete()
        if (::root.isInitialized) render()
    }

    override fun onDestroy() {
        stopRepeatDelete()
        scope.cancel()
        super.onDestroy()
    }
}
