/**
 * The Android app the site offers, from the repository's GitHub release. For a new APK,
 * raise versionName and versionCode in code/android/app/build.gradle.kts, publish a
 * release with the file dcai-guardian-<version>.apk, then change APK_VERSION here.
 * An empty APK_URL turns the download button into "coming soon".
 */
export const APK_VERSION = "0.3.4";
export const APK_URL = `https://github.com/eziedutech/dcai/releases/download/v${APK_VERSION}/dcai-guardian-${APK_VERSION}.apk`;
