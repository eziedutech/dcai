package dev.eziedutech.dcai.samplechat

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Rect
import android.graphics.RectF
import android.graphics.Shader
import android.graphics.Typeface
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.Message
import android.os.Messenger
import androidx.core.content.FileProvider
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.withTimeoutOrNull
import java.io.File

const val GUARDIAN = "dev.eziedutech.dcai.guardian"

/** What dcAI decided for one image. Regions are fractions of the image (l, t, r, b). */
data class ImageDecision(
    val action: String,
    val category: String,
    val score: Int,
    val modelVersion: String,
    val blurAll: Boolean,
    val regions: List<RectF>,
) {
    val blurred get() = action == "dikaburkan"
}

/**
 * The image half of the dcAI SDK, as an integrating app would ship it: bind to dcAI
 * Guardian, hand over a content URI with a read grant, wait for the decision. The image
 * stays on the phone; Guardian reads it in memory.
 */
class DcaiImageClient(private val context: Context) {
    private var service: Messenger? = null
    private var nextId = 1
    private val pending = mutableMapOf<Int, CompletableDeferred<ImageDecision>>()

    private val replies = Messenger(
        object : Handler(Looper.getMainLooper()) {
            override fun handleMessage(msg: Message) {
                if (msg.what != MSG_RESULT) return
                val d = msg.data
                val flat = d.getFloatArray("regions") ?: FloatArray(0)
                val regions = (0 until flat.size / 4).map { i -> RectF(flat[4 * i], flat[4 * i + 1], flat[4 * i + 2], flat[4 * i + 3]) }
                pending.remove(msg.arg1)?.complete(
                    ImageDecision(
                        action = d.getString("action") ?: "dibiarkan",
                        category = d.getString("category") ?: "aman",
                        score = d.getInt("score"),
                        modelVersion = d.getString("model_version") ?: "",
                        blurAll = d.getBoolean("blur_all"),
                        regions = regions,
                    ),
                )
            }
        },
    )

    private val connection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, binder: IBinder?) {
            service = binder?.let(::Messenger)
        }

        override fun onServiceDisconnected(name: ComponentName?) {
            service = null
        }
    }

    fun bind(): Boolean = runCatching {
        context.bindService(
            Intent().setClassName(GUARDIAN, "$GUARDIAN.ingest.ImageCheckService"),
            connection,
            Context.BIND_AUTO_CREATE,
        )
    }.getOrDefault(false)

    fun unbind() {
        runCatching { context.unbindService(connection) }
        service = null
    }

    /** Null when dcAI is not installed or did not answer in time; the app shows the image. */
    suspend fun check(uri: Uri, trigger: String, thread: String, channel: String, sender: String): ImageDecision? {
        val target = service ?: return null
        context.grantUriPermission(GUARDIAN, uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
        val id = nextId++
        val result = CompletableDeferred<ImageDecision>()
        pending[id] = result
        val msg = Message.obtain(null, MSG_CHECK, id, 0).apply {
            data = Bundle().apply {
                putString("uri", uri.toString())
                putString("trigger", trigger)
                putString("thread", thread)
                putString("app", context.packageName)
                putString("channel", channel)
                putString("sender", sender)
                putBoolean("contact_known", false)
            }
            replyTo = replies
        }
        return try {
            target.send(msg)
            withTimeoutOrNull(20_000) { result.await() }
        } catch (_: Exception) {
            null
        } finally {
            pending.remove(id)
            context.revokeUriPermission(GUARDIAN, uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
    }

    /** Opens dcAI's review screen, where the parent decides with the PIN. */
    fun reviewIntent(uri: Uri, decision: ImageDecision): Intent =
        Intent().setClassName(GUARDIAN, "$GUARDIAN.vision.ReviewActivity")
            .setData(uri)
            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            .putExtra("category", decision.category)
            .putExtra("score", decision.score)
            .putExtra("model_version", decision.modelVersion)

    private companion object {
        const val MSG_CHECK = 1
        const val MSG_RESULT = 2
    }
}

/** Blurring as the app shows it: coarse pixels over each region, or over everything. */
object Blur {
    fun apply(source: Bitmap, decision: ImageDecision?): Bitmap {
        if (decision == null || !decision.blurred) return source
        if (decision.blurAll) return pixelate(source, maxOf(source.width, source.height) / 6)
        val out = source.copy(Bitmap.Config.ARGB_8888, true)
        val canvas = Canvas(out)
        for (r in decision.regions) {
            val rect = Rect(
                (r.left * out.width).toInt(), (r.top * out.height).toInt(),
                (r.right * out.width).toInt().coerceAtMost(out.width), (r.bottom * out.height).toInt().coerceAtMost(out.height),
            )
            if (rect.width() <= 0 || rect.height() <= 0) continue
            val piece = Bitmap.createBitmap(source, rect.left, rect.top, rect.width(), rect.height())
            canvas.drawBitmap(pixelate(piece, maxOf(8, rect.height() / 2)), null, rect, null)
        }
        return out
    }

    private fun pixelate(bitmap: Bitmap, block: Int): Bitmap {
        val w = maxOf(1, bitmap.width / block)
        val h = maxOf(1, bitmap.height / block)
        val small = Bitmap.createScaledBitmap(bitmap, w, h, true)
        return Bitmap.createScaledBitmap(small, bitmap.width, bitmap.height, false)
    }
}

/**
 * Synthetic, safe pictures drawn on the phone for the demo: a made-up student card, a
 * landscape, and a screenshot of an invitation to move to another app. Every name, number
 * and address is invented.
 */
object SampleImages {
    fun studentCard(context: Context): Uri = save(context, "kartu.png", 900, 560) { c, w, h ->
        c.drawColor(Color.rgb(232, 240, 254))
        val band = Paint().apply { color = Color.rgb(31, 58, 95) }
        c.drawRect(0f, 0f, w.toFloat(), 110f, band)
        text(c, "KARTU PELAJAR", 40f, 75f, 52f, Color.WHITE, bold = true)
        text(c, "SMP Negeri 5 Makassar", 40f, 190f, 44f, Color.rgb(20, 35, 58), bold = true)
        text(c, "Nama: Rani Putri", 40f, 270f, 42f, Color.rgb(20, 35, 58))
        text(c, "Jl. Mawar No. 12", 40f, 345f, 42f, Color.rgb(20, 35, 58))
        text(c, "HP 0812-3456-7890", 40f, 420f, 42f, Color.rgb(20, 35, 58))
        text(c, "Berlaku 2026", 40f, 500f, 34f, Color.rgb(90, 100, 120))
    }

    fun landscape(context: Context): Uri = save(context, "pemandangan.png", 900, 560) { c, w, h ->
        val sky = Paint().apply { shader = LinearGradient(0f, 0f, 0f, h.toFloat(), Color.rgb(125, 196, 255), Color.rgb(255, 224, 178), Shader.TileMode.CLAMP) }
        c.drawRect(0f, 0f, w.toFloat(), h.toFloat(), sky)
        c.drawCircle(700f, 150f, 70f, Paint().apply { color = Color.rgb(255, 200, 60) })
        val hill = Paint().apply { color = Color.rgb(76, 160, 90); isAntiAlias = true }
        c.drawOval(RectF(-200f, 360f, 600f, 800f), hill)
        c.drawOval(RectF(300f, 400f, 1100f, 860f), hill.apply { color = Color.rgb(56, 132, 74) })
    }

    fun invitation(context: Context): Uri = save(context, "ajakan.png", 900, 560) { c, _, _ ->
        c.drawColor(Color.rgb(24, 24, 32))
        text(c, "ayo pindah ke aplikasi lain", 40f, 160f, 46f, Color.WHITE, bold = true)
        text(c, "jangan bilang siapa-siapa ya", 40f, 250f, 46f, Color.WHITE)
        text(c, "add aku: @teman.rahasia", 40f, 360f, 46f, Color.rgb(255, 214, 102), bold = true)
    }

    private fun text(c: Canvas, s: String, x: Float, y: Float, size: Float, color: Int, bold: Boolean = false) {
        val p = Paint().apply {
            this.color = color
            textSize = size
            isAntiAlias = true
            typeface = if (bold) Typeface.DEFAULT_BOLD else Typeface.DEFAULT
        }
        c.drawText(s, x, y, p)
    }

    private fun save(context: Context, name: String, w: Int, h: Int, draw: (Canvas, Int, Int) -> Unit): Uri {
        val dir = File(context.cacheDir, "images").apply { mkdirs() }
        val file = File(dir, name)
        if (!file.exists()) {
            val bitmap = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
            draw(Canvas(bitmap), w, h)
            file.outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
        }
        return FileProvider.getUriForFile(context, "${context.packageName}.images", file)
    }
}
