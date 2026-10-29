plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "dev.eziedutech.dcai.guardian"
    compileSdk {
        version = release(37) { minorApiLevel = 2 }
    }

    defaultConfig {
        applicationId = "dev.eziedutech.dcai.guardian"
        minSdk = 30
        targetSdk = 36
        // Raise both for every APK published; the site's download button names this version.
        versionCode = 3
        versionName = "0.2.1"
        // The backend as seen from the Android emulator. A real phone sets it during setup.
        buildConfigField("String", "DEFAULT_SERVER", "\"http://10.0.2.2:8000\"")
    }

    // Release signing comes from the environment (the keystore never enters the repo).
    // Without it, as in CI, the release build stays unsigned.
    val keystore = System.getenv("DCAI_KEYSTORE")
    signingConfigs {
        if (keystore != null) {
            create("release") {
                storeFile = file(keystore)
                storePassword = System.getenv("DCAI_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("DCAI_KEY_ALIAS")
                keyPassword = System.getenv("DCAI_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            if (keystore != null) signingConfig = signingConfigs.getByName("release")
            // The public deployment; debug builds keep the emulator's host machine.
            buildConfigField("String", "DEFAULT_SERVER", "\"https://dcai.digitalsafe.app\"")
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    testOptions {
        unitTests.isReturnDefaultValues = true
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.runtime)
    implementation(libs.androidx.lifecycle.compose)
    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.material3)
    implementation(libs.compose.icons)
    implementation(libs.compose.ui.tooling.preview)
    debugImplementation(libs.compose.ui.tooling)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.kotlinx.coroutines.android)
    implementation(libs.okhttp)
    implementation(libs.okhttp.sse)
    // Bundled on-device models: no download at runtime, nothing leaves the phone.
    implementation(libs.mlkit.face)
    implementation(libs.mlkit.text)

    testImplementation(libs.junit)
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.okhttp.mockwebserver)
}
