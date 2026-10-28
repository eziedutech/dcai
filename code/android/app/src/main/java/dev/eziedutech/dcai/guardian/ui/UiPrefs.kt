package dev.eziedutech.dcai.guardian.ui

import android.app.LocaleManager
import android.content.Context
import android.content.res.Configuration
import android.os.Build
import android.os.LocaleList
import androidx.activity.ComponentActivity
import androidx.core.content.edit
import java.util.Locale

/**
 * App language and theme. Kept apart from GuardianStore, so they survive unpairing.
 * Language "system" follows the phone; Indonesian is the default for any other language.
 */
class UiPrefs(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences("dcai_ui", Context.MODE_PRIVATE)

    var language: String
        get() = prefs.getString(KEY_LANGUAGE, SYSTEM) ?: SYSTEM
        set(value) = prefs.edit { putString(KEY_LANGUAGE, value) }

    var theme: String
        get() = prefs.getString(KEY_THEME, SYSTEM) ?: SYSTEM
        set(value) = prefs.edit { putString(KEY_THEME, value) }

    companion object {
        const val SYSTEM = "system"
        private const val KEY_LANGUAGE = "language"
        private const val KEY_THEME = "theme"
    }
}

object AppLocale {
    val CHOICES = listOf(UiPrefs.SYSTEM, "id", "en")

    /**
     * Android 13 and later keep a per-app language (also shown in the phone's settings).
     * Older phones get it from [wrap] in each activity.
     */
    fun set(activity: ComponentActivity, language: String) {
        UiPrefs(activity).language = language
        if (Build.VERSION.SDK_INT >= 33) {
            val tags = if (language == UiPrefs.SYSTEM) LocaleList.getEmptyLocaleList() else LocaleList.forLanguageTags(language)
            activity.getSystemService(LocaleManager::class.java).applicationLocales = tags
        } else {
            activity.recreate()
        }
    }

    fun current(context: Context): String {
        if (Build.VERSION.SDK_INT >= 33) {
            val locales = context.getSystemService(LocaleManager::class.java).applicationLocales
            return if (locales.isEmpty) UiPrefs.SYSTEM else locales[0].language.takeIf { it in CHOICES } ?: UiPrefs.SYSTEM
        }
        return UiPrefs(context).language
    }

    fun wrap(base: Context): Context {
        if (Build.VERSION.SDK_INT >= 33) return base
        val language = UiPrefs(base).language
        if (language == UiPrefs.SYSTEM) return base
        val config = Configuration(base.resources.configuration)
        config.setLocale(Locale.forLanguageTag(language))
        return base.createConfigurationContext(config)
    }
}

/** Every dcAI screen: applies the chosen language on phones older than Android 13. */
open class LocalizedActivity : ComponentActivity() {
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(AppLocale.wrap(newBase))
    }
}
