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
 * The dcAI keyboard. A minimal soft keyboard that also checks the text the child types.
 * It only ever sees the child's own typing in the current app, never the other person's
 * messages. When the child sends (the action key), the buffer is masked on the phone and
 * submitted for assessment, the same path the sample chat app uses.
 *
 * The child knows this keyboard is dcAI: it is named "dcAI" in the keyboard picker and the
 * guardian notification stays visible.
 */
class DcaiKeyboardService : InputMethodService() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private val buffer = StringBuilder()

    private val rows = listOf(
        "qwertyuiop",
        "asdfghjkl",
        "zxcvbnm",
    )

    override fun onCreateInputView(): View {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(8, 8, 8, 24)
        }
        rows.forEach { row ->
            val line = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
            row.forEach { ch -> line.addView(key(ch.toString()) { type(ch.toString()) }, weight()) }
            root.addView(line)
        }
        val last = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        last.addView(key("space") { type(" ") }, weight(3f))
        last.addView(key("del") { backspace() }, weight())
        last.addView(key(getString(dev.eziedutech.dcai.guardian.R.string.keyboard_check)) { send() }, weight(2f))
        root.addView(last)
        return root
    }

    private fun key(label: String, onClick: () -> Unit) = Button(this).apply {
        text = label
        isAllCaps = false
        setOnClickListener { onClick() }
    }

    private fun weight(w: Float = 1f) =
        LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, w).apply { gravity = Gravity.CENTER }

    private fun type(text: String) {
        currentInputConnection?.commitText(text, 1)
        buffer.append(text)
    }

    private fun backspace() {
        currentInputConnection?.deleteSurroundingText(1, 0)
        if (buffer.isNotEmpty()) buffer.deleteCharAt(buffer.length - 1)
    }

    /** Commit a newline to the field and hand the typed text to dcAI. */
    private fun send() {
        val text = buffer.toString().trim()
        currentInputConnection?.commitText("\n", 1)
        buffer.clear()
        if (text.isEmpty()) return
        val ingest = ServiceLocator.ingest(this) ?: return
        val targetApp = currentInputEditorInfo?.packageName ?: "unknown.app"
        scope.launch {
            runCatching {
                ingest.submit(
                    threadId = targetApp,
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
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }
}
