package dev.eziedutech.dcai.guardian.ui.art

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import dev.eziedutech.dcai.guardian.ui.theme.BrandBlue
import dev.eziedutech.dcai.guardian.ui.theme.BrandLeaf

/**
 * Flat illustrations in the logo's colours, drawn on a 100 x 100 grid so they scale to any
 * size. Each is decorative: screens carry their meaning in text.
 */
enum class Art { SHIELD, SHIELD_WARN, CHAT, IMAGE, SITE, VOICE, KEYBOARD, FAMILY, CONSENT, PIN, NUDGE, TIP, EYE }

private val Sky = Color(0xFFDCE5FB)
private val Mint = Color(0xFFCFF2E8)
private val Sun = Color(0xFFF2A93B)
private val Peach = Color(0xFFFFD9B3)
private val Ink = Color(0xFF13306F)
private val Paper = Color.White

@Composable
fun Illustration(art: Art, modifier: Modifier = Modifier) {
    Canvas(modifier.aspectRatio(1f)) {
        val u = size.minDimension / 100f
        backdrop(u)
        when (art) {
            Art.SHIELD -> shieldScene(u, warn = false)
            Art.SHIELD_WARN -> shieldScene(u, warn = true)
            Art.CHAT -> chat(u)
            Art.IMAGE -> image(u)
            Art.SITE -> site(u)
            Art.VOICE -> voice(u)
            Art.KEYBOARD -> keyboard(u)
            Art.FAMILY -> family(u)
            Art.CONSENT -> consent(u)
            Art.PIN -> pin(u)
            Art.NUDGE -> nudge(u)
            Art.TIP -> tip(u)
            Art.EYE -> eye(u)
        }
    }
}

private fun DrawScope.p(u: Float, x: Float, y: Float) = Offset(x * u, y * u)

private fun DrawScope.backdrop(u: Float) {
    drawCircle(Brush.linearGradient(listOf(Sky, Mint), p(u, 10f, 10f), p(u, 90f, 90f)), 46f * u, p(u, 50f, 52f))
    drawCircle(Paper.copy(alpha = 0.55f), 6f * u, p(u, 18f, 22f))
    drawCircle(Sun.copy(alpha = 0.85f), 3.2f * u, p(u, 86f, 24f))
    drawCircle(BrandLeaf.copy(alpha = 0.5f), 2.4f * u, p(u, 14f, 76f))
}

private fun shieldPath(u: Float, cx: Float, top: Float, w: Float, h: Float) = Path().apply {
    val l = (cx - w / 2) * u
    val r = (cx + w / 2) * u
    val t = top * u
    val b = (top + h) * u
    moveTo(cx * u, t)
    cubicTo(cx * u + w * 0.18f * u, t + h * 0.08f * u, r - w * 0.05f * u, t + h * 0.1f * u, r, t + h * 0.12f * u)
    cubicTo(r, t + h * 0.55f * u, cx * u + w * 0.3f * u, b - h * 0.12f * u, cx * u, b)
    cubicTo(cx * u - w * 0.3f * u, b - h * 0.12f * u, l, t + h * 0.55f * u, l, t + h * 0.12f * u)
    cubicTo(l + w * 0.05f * u, t + h * 0.1f * u, cx * u - w * 0.18f * u, t + h * 0.08f * u, cx * u, t)
    close()
}

private fun DrawScope.leaf(u: Float, x: Float, y: Float, s: Float, angle: Float = -30f) {
    rotate(angle, p(u, x, y)) {
        val path = Path().apply {
            moveTo(x * u, (y - s) * u)
            quadraticTo((x + s * 0.7f) * u, y * u, x * u, (y + s) * u)
            quadraticTo((x - s * 0.7f) * u, y * u, x * u, (y - s) * u)
            close()
        }
        drawPath(path, BrandLeaf)
        drawLine(Paper.copy(alpha = 0.7f), p(u, x, y - s * 0.7f), p(u, x, y + s * 0.8f), 0.8f * u, StrokeCap.Round)
    }
}

private fun DrawScope.check(u: Float, cx: Float, cy: Float, s: Float, color: Color = Paper) {
    val path = Path().apply {
        moveTo((cx - s) * u, cy * u)
        lineTo((cx - s * 0.25f) * u, (cy + s * 0.75f) * u)
        lineTo((cx + s * 1.1f) * u, (cy - s * 0.8f) * u)
    }
    drawPath(path, color, style = Stroke(s * 0.45f * u, cap = StrokeCap.Round, join = StrokeJoin.Round))
}

private fun DrawScope.badge(u: Float, cx: Float, cy: Float, r: Float, warn: Boolean = false) {
    drawCircle(Paper, (r + 1.6f) * u, p(u, cx, cy))
    drawCircle(if (warn) Sun else BrandLeaf, r * u, p(u, cx, cy))
    if (warn) {
        drawLine(Paper, p(u, cx, cy - r * 0.5f), p(u, cx, cy + r * 0.12f), r * 0.28f * u, StrokeCap.Round)
        drawCircle(Paper, r * 0.16f * u, p(u, cx, cy + r * 0.5f))
    } else {
        check(u, cx, cy, r * 0.45f)
    }
}

private fun DrawScope.shieldScene(u: Float, warn: Boolean) {
    drawPath(shieldPath(u, 50f, 16f, 54f, 66f), Brush.verticalGradient(listOf(BrandBlue, Color(0xFF2E66D6)), 16f * u, 82f * u))
    drawPath(shieldPath(u, 50f, 22f, 42f, 52f), Paper.copy(alpha = 0.16f))
    leaf(u, 35f, 62f, 13f, angle = -35f)
    if (warn) {
        drawLine(Paper, p(u, 50f, 34f), p(u, 50f, 52f), 6f * u, StrokeCap.Round)
        drawCircle(Paper, 3.4f * u, p(u, 50f, 62f))
    } else {
        check(u, 49f, 47f, 10f)
    }
    // sparkles
    for ((x, y, s) in listOf(Triple(82f, 44f, 3f), Triple(20f, 40f, 2.2f), Triple(76f, 76f, 2f))) {
        drawLine(Sun, p(u, x - s, y), p(u, x + s, y), 1.2f * u, StrokeCap.Round)
        drawLine(Sun, p(u, x, y - s), p(u, x, y + s), 1.2f * u, StrokeCap.Round)
    }
}

private fun DrawScope.bubble(u: Float, x: Float, y: Float, w: Float, h: Float, color: Color, tailLeft: Boolean) {
    drawRoundRect(color, p(u, x, y), Size(w * u, h * u), CornerRadius(7f * u))
    val tx = if (tailLeft) x + 6f else x + w - 6f
    val tail = Path().apply {
        moveTo(tx * u - 3f * u, (y + h - 1f) * u)
        lineTo((if (tailLeft) tx - 5f else tx + 5f) * u, (y + h + 6f) * u)
        lineTo(tx * u + 3f * u, (y + h - 1f) * u)
        close()
    }
    drawPath(tail, color)
}

private fun DrawScope.chat(u: Float) {
    bubble(u, 16f, 24f, 46f, 22f, Paper, tailLeft = true)
    for (i in 0..2) drawCircle(BrandBlue.copy(alpha = 0.55f), 2.6f * u, p(u, 29f + i * 10f, 35f))
    bubble(u, 38f, 52f, 46f, 22f, BrandBlue, tailLeft = false)
    drawRoundRect(Paper.copy(alpha = 0.85f), p(u, 45f, 59f), Size(26f * u, 3f * u), CornerRadius(2f * u))
    drawRoundRect(Paper.copy(alpha = 0.6f), p(u, 45f, 65f), Size(18f * u, 3f * u), CornerRadius(2f * u))
    drawPath(shieldPath(u, 22f, 60f, 16f, 19f), BrandLeaf)
    check(u, 21.6f, 68.5f, 3.2f)
}

private fun DrawScope.image(u: Float) {
    drawRoundRect(Paper, p(u, 18f, 24f), Size(64f * u, 50f * u), CornerRadius(7f * u))
    drawRoundRect(Sky, p(u, 23f, 29f), Size(54f * u, 40f * u), CornerRadius(4f * u))
    drawCircle(Sun, 5f * u, p(u, 66f, 38f))
    val hill = Path().apply {
        moveTo(23f * u, 69f * u); lineTo(40f * u, 47f * u); lineTo(52f * u, 60f * u); lineTo(60f * u, 52f * u); lineTo(77f * u, 69f * u); close()
    }
    drawPath(hill, BrandLeaf)
    // the blurred corner: coarse squares
    val colors = listOf(BrandBlue.copy(alpha = 0.35f), BrandBlue.copy(alpha = 0.55f), BrandBlue.copy(alpha = 0.25f))
    for (i in 0..2) for (j in 0..1) {
        drawRect(colors[(i + j) % 3], p(u, 23f + i * 7f, 29f + j * 7f), Size(7f * u, 7f * u))
    }
    badge(u, 78f, 72f, 8f)
}

private fun DrawScope.site(u: Float) {
    drawRoundRect(Paper, p(u, 14f, 22f), Size(72f * u, 56f * u), CornerRadius(7f * u))
    drawRoundRect(BrandBlue, p(u, 14f, 22f), Size(72f * u, 11f * u), CornerRadius(7f * u))
    drawRect(BrandBlue, p(u, 14f, 28f), Size(72f * u, 5f * u))
    for (i in 0..2) drawCircle(Paper.copy(alpha = 0.8f), 1.6f * u, p(u, 21f + i * 5f, 27.5f))
    val c = p(u, 42f, 56f)
    drawCircle(Sky, 15f * u, c)
    drawCircle(BrandBlue, 15f * u, c, style = Stroke(2.2f * u))
    drawOval(BrandBlue, p(u, 35f, 41f), Size(14f * u, 30f * u), style = Stroke(1.8f * u))
    drawLine(BrandBlue, p(u, 27f, 56f), p(u, 57f, 56f), 1.8f * u)
    drawLine(BrandBlue, p(u, 29f, 48f), p(u, 55f, 48f), 1.4f * u)
    drawLine(BrandBlue, p(u, 29f, 64f), p(u, 55f, 64f), 1.4f * u)
    // lock
    drawRoundRect(BrandLeaf, p(u, 62f, 54f), Size(16f * u, 13f * u), CornerRadius(3f * u))
    drawArc(BrandLeaf, 180f, 180f, false, p(u, 64.5f, 46f), Size(11f * u, 14f * u), style = Stroke(2.4f * u))
    drawCircle(Paper, 1.8f * u, p(u, 70f, 60f))
}

private fun DrawScope.voice(u: Float) {
    drawRoundRect(BrandBlue, p(u, 41f, 22f), Size(18f * u, 32f * u), CornerRadius(9f * u))
    drawArc(BrandBlue, 0f, 180f, false, p(u, 33f, 34f), Size(34f * u, 30f * u), style = Stroke(3f * u, cap = StrokeCap.Round))
    drawLine(BrandBlue, p(u, 50f, 64f), p(u, 50f, 74f), 3f * u, StrokeCap.Round)
    drawLine(BrandBlue, p(u, 42f, 75f), p(u, 58f, 75f), 3f * u, StrokeCap.Round)
    for ((i, h) in listOf(6f, 12f, 8f).withIndex()) {
        drawLine(BrandLeaf, p(u, 18f + i * 5f, 44f - h / 2), p(u, 18f + i * 5f, 44f + h / 2), 2.4f * u, StrokeCap.Round)
        drawLine(BrandLeaf, p(u, 82f - i * 5f, 44f - h / 2), p(u, 82f - i * 5f, 44f + h / 2), 2.4f * u, StrokeCap.Round)
    }
}

private fun DrawScope.keyboard(u: Float) {
    drawRoundRect(Paper, p(u, 14f, 36f), Size(72f * u, 40f * u), CornerRadius(7f * u))
    for (row in 0..2) for (col in 0..6) {
        val x = 19f + col * 9.5f
        val y = 41f + row * 9.5f
        if (row == 2 && col in 2..4) continue
        drawRoundRect(if ((row + col) % 4 == 0) Mint else Sky, p(u, x, y), Size(7f * u, 7f * u), CornerRadius(1.6f * u))
    }
    drawRoundRect(BrandBlue, p(u, 38f, 60f), Size(26f * u, 7f * u), CornerRadius(1.6f * u))
    bubble(u, 26f, 14f, 40f, 15f, BrandLeaf, tailLeft = false)
    check(u, 45f, 21f, 3.4f)
}

private fun DrawScope.person(u: Float, x: Float, y: Float, s: Float, body: Color, skin: Color = Peach) {
    drawRoundRect(body, p(u, x - 11f * s, y), Size(22f * s * u, 26f * s * u), CornerRadius(11f * s * u))
    drawCircle(skin, 8f * s * u, p(u, x, y - 8f * s))
}

private fun DrawScope.family(u: Float) {
    person(u, 37f, 44f, 1.15f, BrandBlue)
    person(u, 64f, 55f, 0.85f, BrandLeaf)
    val heart = Path().apply {
        moveTo(52f * u, 30f * u)
        cubicTo(46f * u, 22f * u, 38f * u, 30f * u, 52f * u, 39f * u)
        cubicTo(66f * u, 30f * u, 58f * u, 22f * u, 52f * u, 30f * u)
        close()
    }
    drawPath(heart, Sun)
    drawRoundRect(Paper, p(u, 22f, 78f), Size(56f * u, 5f * u), CornerRadius(3f * u))
}

private fun DrawScope.consent(u: Float) {
    drawRoundRect(Paper, p(u, 26f, 16f), Size(48f * u, 64f * u), CornerRadius(6f * u))
    drawRoundRect(BrandBlue, p(u, 33f, 25f), Size(26f * u, 4f * u), CornerRadius(2f * u))
    for (i in 0..4) {
        drawRoundRect(Sky, p(u, 33f, 35f + i * 7f), Size((34f - (i % 2) * 8f) * u, 3f * u), CornerRadius(2f * u))
    }
    badge(u, 70f, 72f, 10f)
}

private fun DrawScope.pin(u: Float) {
    drawArc(BrandBlue, 180f, 180f, false, p(u, 35f, 22f), Size(30f * u, 34f * u), style = Stroke(5f * u))
    drawRoundRect(BrandBlue, p(u, 27f, 40f), Size(46f * u, 38f * u), CornerRadius(8f * u))
    for (i in 0..3) drawCircle(Paper, 3f * u, p(u, 36f + i * 9.3f, 59f))
    leaf(u, 74f, 76f, 9f, angle = 30f)
}

private fun DrawScope.nudge(u: Float) {
    bubble(u, 20f, 26f, 60f, 36f, Paper, tailLeft = true)
    drawCircle(Sun, 9f * u, p(u, 36f, 44f))
    drawCircle(Ink, 1.3f * u, p(u, 33f, 42f))
    drawCircle(Ink, 1.3f * u, p(u, 39f, 42f))
    drawArc(Ink, 20f, 140f, false, p(u, 31.5f, 42f), Size(9f * u, 6f * u), style = Stroke(1.3f * u, cap = StrokeCap.Round))
    drawRoundRect(BrandBlue.copy(alpha = 0.6f), p(u, 50f, 38f), Size(22f * u, 3.2f * u), CornerRadius(2f * u))
    drawRoundRect(BrandLeaf.copy(alpha = 0.7f), p(u, 50f, 46f), Size(16f * u, 3.2f * u), CornerRadius(2f * u))
}

private fun DrawScope.tip(u: Float) {
    drawCircle(Sun, 16f * u, p(u, 50f, 42f))
    drawRoundRect(BrandBlue, p(u, 43f, 57f), Size(14f * u, 9f * u), CornerRadius(2.5f * u))
    drawRoundRect(BrandBlue.copy(alpha = 0.7f), p(u, 45f, 67f), Size(10f * u, 4f * u), CornerRadius(2f * u))
    for (a in listOf(-60f, -30f, 0f, 30f, 60f)) {
        rotate(a, p(u, 50f, 42f)) { drawLine(Sun, p(u, 50f, 18f), p(u, 50f, 13f), 2.4f * u, StrokeCap.Round) }
    }
    leaf(u, 62f, 70f, 7f, angle = 40f)
}

private fun DrawScope.eye(u: Float) {
    val eye = Path().apply {
        moveTo(18f * u, 50f * u)
        quadraticTo(50f * u, 20f * u, 82f * u, 50f * u)
        quadraticTo(50f * u, 80f * u, 18f * u, 50f * u)
        close()
    }
    drawPath(eye, Paper)
    drawCircle(BrandBlue, 12f * u, p(u, 50f, 50f))
    drawCircle(Ink, 5f * u, p(u, 50f, 50f))
    drawCircle(Paper, 2f * u, p(u, 53f, 47f))
    drawRect(BrandLeaf, Rect(p(u, 30f, 76f), p(u, 70f, 79f)).topLeft, Size(40f * u, 3f * u))
}
