plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "dev.eziedutech.dcai.samplechat"
    compileSdk {
        version = release(37) { minorApiLevel = 2 }
    }
    defaultConfig {
        applicationId = "dev.eziedutech.dcai.samplechat"
        minSdk = 30
        targetSdk = 36
        // Same version as dcAI Guardian; published beside it for demos on a real phone.
        versionCode = 3
        versionName = "0.2.1"
    }

    // Signed with the same key as dcAI Guardian, from the environment, so the signature
    // permission to hand messages to dcAI is granted. Without it the release is unsigned.
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
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"))
        }
    }
    buildFeatures { compose = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.material3)
    implementation(libs.compose.icons)
    implementation(libs.compose.ui.tooling.preview)
    debugImplementation(libs.compose.ui.tooling)
    implementation(libs.kotlinx.coroutines.android)
}
