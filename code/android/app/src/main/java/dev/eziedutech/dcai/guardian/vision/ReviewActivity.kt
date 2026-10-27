package dev.eziedutech.dcai.guardian.vision

import android.app.Activity
import android.graphics.Bitmap
import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.eziedutech.dcai.guardian.R
import dev.eziedutech.dcai.guardian.ServiceLocator
import dev.eziedutech.dcai.guardian.net.DetectionFeedbackRequest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * A blurred image, reviewed together with the parent on the child's phone. The child asks
 * from the chat app; the parent enters the PIN, looks, and decides. A false detection is
 * remembered on this phone (tier 1) and reported to the server as a label and a score,
 * without the image (tier 2). The image is never stored or sent, and the screen blocks
 * screenshots while it is open.
 */
class ReviewActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.setFlags(WindowManager.LayoutParams.FLAG_SECURE, WindowManager.LayoutParams.FLAG_SECURE)
        val uri = intent.data
        val category = Category.entries.firstOrNull { it.wire == intent.getStringExtra(EXTRA_CATEGORY) }
        if (uri == null || category == null || category == Category.AMAN) {
            finish()
            return
        }
        val score = intent.getIntExtra(EXTRA_SCORE, 0).coerceIn(0, 100)
        val modelVersion = intent.getStringExtra(EXTRA_MODEL_VERSION)?.take(120)?.ifBlank { null } ?: OnDeviceDetectors.VERSION

        setContent {
            MaterialTheme {
                Surface(Modifier.fillMaxSize()) {
                    ReviewScreen(
                        hasPin = ServiceLocator.store(this).hasPin,
                        checkPin = { ServiceLocator.store(this).checkPin(it) },
                        load = { withContext(Dispatchers.IO) { Bitmaps.decode(contentResolver, uri) } },
                        onKeep = { setResult(Activity.RESULT_CANCELED); finish() },
                        onFalseDetection = { bitmap ->
                            ServiceLocator.store(this).recordFalseDetection(Bitmaps.dHash(bitmap), category)
                            ServiceLocator.client(this)?.let { client ->
                                runCatching {
                                    client.sendDetectionFeedback(
                                        DetectionFeedbackRequest(category = category.wire, score = score, modelVersion = modelVersion),
                                    )
                                }
                            }
                            setResult(Activity.RESULT_OK)
                            finish()
                        },
                    )
                }
            }
        }
    }

    companion object {
        const val EXTRA_CATEGORY = "category"
        const val EXTRA_SCORE = "score"
        const val EXTRA_MODEL_VERSION = "model_version"
        const val MAX_ATTEMPTS = 5
    }
}

@Composable
private fun ReviewScreen(
    hasPin: Boolean,
    checkPin: (String) -> Boolean,
    load: suspend () -> Bitmap?,
    onKeep: () -> Unit,
    onFalseDetection: suspend (Bitmap) -> Unit,
) {
    val scope = rememberCoroutineScope()
    var pin by remember { mutableStateOf("") }
    var attempts by remember { mutableIntStateOf(0) }
    var bitmap by remember { mutableStateOf<Bitmap?>(null) }
    var error by remember { mutableStateOf<Int?>(null) }
    var busy by remember { mutableStateOf(false) }

    Column(
        Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(stringResource(R.string.review_title), fontSize = 24.sp, fontWeight = FontWeight.ExtraBold)
        if (!hasPin) {
            Text(stringResource(R.string.review_no_pin))
            OutlinedButton(onClick = onKeep) { Text(stringResource(R.string.review_close)) }
            return@Column
        }
        val shown = bitmap
        if (shown == null) {
            Text(stringResource(R.string.review_lead))
            OutlinedTextField(
                value = pin, onValueChange = { pin = it.filter(Char::isDigit).take(8) },
                label = { Text(stringResource(R.string.review_pin)) },
                singleLine = true, modifier = Modifier.fillMaxWidth(),
                visualTransformation = PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
            )
            error?.let { Text(stringResource(it), color = MaterialTheme.colorScheme.error) }
            Button(
                onClick = {
                    busy = true
                    scope.launch {
                        val ok = withContext(Dispatchers.Default) { checkPin(pin) }
                        pin = ""
                        if (ok) {
                            bitmap = load()
                            if (bitmap == null) error = R.string.review_unreadable
                        } else {
                            attempts++
                            error = R.string.review_wrong_pin
                            if (attempts >= ReviewActivity.MAX_ATTEMPTS) onKeep()
                        }
                        busy = false
                    }
                },
                enabled = !busy && pin.length >= 4,
                modifier = Modifier.fillMaxWidth(),
            ) { Text(stringResource(R.string.review_open)) }
            OutlinedButton(onClick = onKeep, modifier = Modifier.fillMaxWidth()) { Text(stringResource(R.string.review_close)) }
        } else {
            Image(shown.asImageBitmap(), contentDescription = null, modifier = Modifier.fillMaxWidth().heightIn(max = 420.dp))
            Text(stringResource(R.string.review_decide))
            Button(onClick = onKeep, modifier = Modifier.fillMaxWidth()) { Text(stringResource(R.string.review_keep)) }
            OutlinedButton(
                onClick = { busy = true; scope.launch { onFalseDetection(shown) } },
                enabled = !busy,
                modifier = Modifier.fillMaxWidth(),
            ) { Text(stringResource(R.string.review_false)) }
        }
    }
}
