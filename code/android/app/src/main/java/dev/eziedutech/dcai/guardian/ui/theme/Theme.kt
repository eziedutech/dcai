package dev.eziedutech.dcai.guardian.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** The two colours of the dcAI logo. */
val BrandBlue = Color(0xFF1C48AB)
val BrandLeaf = Color(0xFF18A88D)

/** Status colours used by indicators, the same in light and dark. */
@Immutable
data class StatusColors(val on: Color, val warn: Color, val off: Color, val onSoft: Color, val warnSoft: Color, val offSoft: Color)

private val LightStatus = StatusColors(
    on = Color(0xFF138A72), warn = Color(0xFFC77700), off = Color(0xFF7A8496),
    onSoft = Color(0xFFD5F3EB), warnSoft = Color(0xFFFFEBCC), offSoft = Color(0xFFE8ECF2),
)
private val DarkStatus = StatusColors(
    on = Color(0xFF5DD8B7), warn = Color(0xFFFFB84D), off = Color(0xFF9AA4B5),
    onSoft = Color(0xFF123D35), warnSoft = Color(0xFF45320F), offSoft = Color(0xFF263044),
)

val LocalStatusColors = staticCompositionLocalOf { LightStatus }

private val Light = lightColorScheme(
    primary = BrandBlue,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFDCE5FB),
    onPrimaryContainer = Color(0xFF0B2566),
    secondary = BrandLeaf,
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFCFF2E8),
    onSecondaryContainer = Color(0xFF00382D),
    tertiary = Color(0xFFF2A93B),
    tertiaryContainer = Color(0xFFFFE9C7),
    onTertiaryContainer = Color(0xFF4A2C00),
    background = Color(0xFFF5F7FC),
    onBackground = Color(0xFF131B2E),
    surface = Color.White,
    onSurface = Color(0xFF131B2E),
    surfaceVariant = Color(0xFFEDF1F8),
    onSurfaceVariant = Color(0xFF4F5A6E),
    surfaceContainer = Color(0xFFF0F3FA),
    surfaceContainerHigh = Color(0xFFE9EEF7),
    outline = Color(0xFFC3CBD9),
    outlineVariant = Color(0xFFDDE3EE),
    error = Color(0xFFC93C3C),
)

private val Dark = darkColorScheme(
    primary = Color(0xFFAFC4FF),
    onPrimary = Color(0xFF0A2463),
    primaryContainer = Color(0xFF203F8F),
    onPrimaryContainer = Color(0xFFDCE5FB),
    secondary = Color(0xFF5DD8B7),
    onSecondary = Color(0xFF00382D),
    secondaryContainer = Color(0xFF0F5446),
    onSecondaryContainer = Color(0xFFCFF2E8),
    tertiary = Color(0xFFFFC76E),
    tertiaryContainer = Color(0xFF5A3C00),
    onTertiaryContainer = Color(0xFFFFE9C7),
    background = Color(0xFF0D1424),
    onBackground = Color(0xFFE3E8F3),
    surface = Color(0xFF151E31),
    onSurface = Color(0xFFE3E8F3),
    surfaceVariant = Color(0xFF1E293F),
    onSurfaceVariant = Color(0xFFB4BED0),
    surfaceContainer = Color(0xFF182237),
    surfaceContainerHigh = Color(0xFF1E2940),
    outline = Color(0xFF4A5670),
    outlineVariant = Color(0xFF2C3750),
    error = Color(0xFFFF8A80),
)

private val Type = Typography().run {
    copy(
        headlineLarge = headlineLarge.copy(fontWeight = FontWeight.ExtraBold, fontSize = 30.sp, lineHeight = 36.sp),
        headlineMedium = headlineMedium.copy(fontWeight = FontWeight.ExtraBold, fontSize = 26.sp, lineHeight = 32.sp),
        headlineSmall = headlineSmall.copy(fontWeight = FontWeight.Bold, fontSize = 22.sp),
        titleLarge = titleLarge.copy(fontWeight = FontWeight.Bold),
        titleMedium = titleMedium.copy(fontWeight = FontWeight.SemiBold),
        labelLarge = labelLarge.copy(fontWeight = FontWeight.SemiBold, fontSize = 15.sp),
        bodyLarge = bodyLarge.copy(lineHeight = 24.sp),
    )
}

private val AppShapes = Shapes(
    small = RoundedCornerShape(12.dp),
    medium = RoundedCornerShape(18.dp),
    large = RoundedCornerShape(24.dp),
    extraLarge = RoundedCornerShape(32.dp),
)

val CaptionStyle = TextStyle(fontSize = 12.sp, lineHeight = 16.sp)

/** theme: "system", "light" or "dark". */
@Composable
fun DcaiTheme(theme: String = "system", content: @Composable () -> Unit) {
    val dark = when (theme) {
        "light" -> false
        "dark" -> true
        else -> isSystemInDarkTheme()
    }
    androidx.compose.runtime.CompositionLocalProvider(LocalStatusColors provides if (dark) DarkStatus else LightStatus) {
        MaterialTheme(colorScheme = if (dark) Dark else Light, typography = Type, shapes = AppShapes, content = content)
    }
}

@Composable
fun isDarkTheme(theme: String): Boolean = when (theme) {
    "light" -> false
    "dark" -> true
    else -> isSystemInDarkTheme()
}
