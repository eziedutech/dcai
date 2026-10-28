package dev.eziedutech.dcai.guardian.ui

import android.provider.Settings
import androidx.compose.foundation.ScrollState
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.compositionLocalOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import dev.eziedutech.dcai.guardian.ui.theme.BrandBlue
import dev.eziedutech.dcai.guardian.ui.theme.BrandLeaf

/**
 * Soft glass. A quiet scene of three colour fields sits behind each screen and surfaces on
 * top are translucent with a hairline edge. Nothing is blurred live: the fields are already
 * soft gradients, so a card over them reads as frosted at no cost while scrolling, on every
 * Android version the app supports.
 */

/** The scroll of the screen in front, for parallax. Null where a screen does not scroll. */
val LocalScroll = compositionLocalOf<ScrollState?> { null }

private val Dark: Boolean
    @Composable get() = MaterialTheme.colorScheme.background.luminance() < 0.3f

/** A colour field drawn once; [depth] moves it against the scroll by that share. */
@Composable
private fun Field(color: Color, x: Float, y: Float, radius: Float, depth: Float) {
    val scroll = LocalScroll.current
    Box(
        Modifier.fillMaxSize()
            .graphicsLayer { translationY = -(scroll?.value ?: 0) * depth }
            .drawBehind {
                val r = size.maxDimension * radius
                val c = Offset(size.width * x, size.height * y)
                drawCircle(Brush.radialGradient(listOf(color, color.copy(alpha = 0f)), center = c, radius = r), r, c)
            },
    )
}

/** The scene behind a screen. Put scrolling content inside and provide its [scroll]. */
@Composable
fun GlassScene(scroll: ScrollState? = null, modifier: Modifier = Modifier, content: @Composable BoxScope.() -> Unit) {
    val dark = Dark
    // "Remove animations" in the phone's settings stops the parallax too.
    val context = LocalContext.current
    val still = remember {
        Settings.Global.getFloat(context.contentResolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f) == 0f
    }
    CompositionLocalProvider(LocalScroll provides if (still) null else scroll) {
        Box(modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {
            Field(BrandBlue.copy(alpha = if (dark) 0.30f else 0.16f), 0.95f, 0.02f, 0.62f, 0.10f)
            Field(BrandLeaf.copy(alpha = if (dark) 0.16f else 0.13f), 0.0f, 0.55f, 0.55f, 0.18f)
            Field(Color(0xFFC9B084).copy(alpha = if (dark) 0.08f else 0.18f), 0.85f, 1.0f, 0.5f, 0.05f)
            content()
        }
    }
}

/** A frosted surface: translucent fill and a light edge. */
@Composable
fun Modifier.glass(shape: Shape = RoundedCornerShape(24.dp), strong: Boolean = false): Modifier {
    val dark = Dark
    val fill = if (dark) MaterialTheme.colorScheme.surface.copy(alpha = if (strong) 0.82f else 0.62f)
    else Color.White.copy(alpha = if (strong) 0.82f else 0.64f)
    val edge = if (dark) Color.White.copy(alpha = 0.08f) else Color.White.copy(alpha = 0.85f)
    return clip(shape).background(fill).border(1.dp, edge, shape)
}

/** A quieter fill for things inside a glass surface. */
@Composable
fun Modifier.glassFill(shape: Shape = RoundedCornerShape(16.dp)): Modifier {
    val dark = Dark
    val fill = if (dark) Color.White.copy(alpha = 0.05f) else Color.White.copy(alpha = 0.55f)
    val edge = if (dark) Color.White.copy(alpha = 0.06f) else Color(0x1214233A)
    return clip(shape).background(fill).border(1.dp, edge, shape)
}

/** Moves by the scroll times [depth]; small values read as depth. */
fun Modifier.parallax(scroll: ScrollState?, depth: Float): Modifier =
    if (scroll == null) this else graphicsLayer { translationY = scroll.value * depth }
