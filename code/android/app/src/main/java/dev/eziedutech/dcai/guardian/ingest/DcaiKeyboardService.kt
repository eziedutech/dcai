package dev.eziedutech.dcai.guardian.ingest

import android.inputmethodservice.InputMethodService
import android.view.Gravity
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
 * and punctuation, so a child can use it as their everyday keyboard. The child knows it is
 * dcAI: it is named "dcAI" in the keyboard picker and the guardian notification stays
 * visible.
 */
class DcaiKeyboardService : InputMethodService() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private val buffer = StringBuilder()

    private enum class Caps { OFF, SHIFT, LOCK }

    private var caps = Caps.OFF
    private var symbols = false
    private lateinit var root: LinearLayout

    private val letterRows = listOf("qwertyuiop", "asdfghjkl", "zxcvbnm")
    // Two symbol rows plus a shorter punctuation row (del sits at its end, like the letters).
    private val symbolRows = listOf("1234567890", "@#\$_&-+()/", "*\"':;!?")

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
        val rows = if (symbols) symbolRows else letterRows
        rows.forEachIndexed { i, chars ->
            val line = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
            // Last row carries Shift (letters only) at the left and Del at the right.
            if (i == rows.lastIndex) {
                if (!symbols) line.addView(key(shiftLabel()) { onShift() }, weight(1.5f))
                chars.forEach { ch -> line.addView(letterKey(ch.toString()), weight()) }
                line.addView(key("⌫") { backspace() }, weight(1.5f))
            } else {
                chars.forEach { ch -> line.addView(letterKey(ch.toString()), weight()) }
            }
            root.addView(line)
        }
        val bottom = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        bottom.addView(key(if (symbols) "ABC" else "?123") { toggleSymbols() }, weight(1.5f))
        bottom.addView(key("space") { type(" ") }, weight(5f))
        bottom.addView(key(".") { type(".") }, weight())
        bottom.addView(key(getString(dev.eziedutech.dcai.guardian.R.string.keyboard_check)) { send() }, weight(2f))
        root.addView(bottom)
    }

    private fun shiftLabel() = if (caps == Caps.LOCK) "⇪" else "⇧"

    private fun letterKey(ch: String): Button {
        val shown = if (!symbols && caps != Caps.OFF) ch.uppercase() else ch
        return key(shown) { type(shown) }
    }

    private fun key(label: String, onClick: () -> Unit) = Button(this).apply {
        text = label
        isAllCaps = false
        setOnClickListener { onClick() }
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

    private fun toggleSymbols() {
        symbols = !symbols
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
        symbols = false
        if (::root.isInitialized) render()
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }
}
