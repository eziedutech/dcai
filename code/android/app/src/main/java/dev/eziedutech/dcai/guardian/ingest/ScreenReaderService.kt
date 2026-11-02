package dev.eziedutech.dcai.guardian.ingest

import android.accessibilityservice.AccessibilityService
import android.content.ComponentName
import android.content.Context
import android.graphics.Bitmap
import android.graphics.Rect
import android.os.SystemClock
import android.provider.Settings
import android.util.Log
import android.view.Display
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import dev.eziedutech.dcai.guardian.R
import dev.eziedutech.dcai.guardian.ServiceLocator
import dev.eziedutech.dcai.guardian.service.Notifications
import dev.eziedutech.dcai.guardian.vision.ScreenBox
import dev.eziedutech.dcai.guardian.vision.ImageContext
import dev.eziedutech.dcai.guardian.vision.ScreenImages
import dev.eziedutech.dcai.guardian.vision.ThreadLevels
import dev.eziedutech.dcai.guardian.vision.Trigger
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

/**
 * The screen-text source agreed in proposal 0002: dcAI reads the text shown on screen in any
 * app, so patterns are recognised whatever app the child chats in, and whatever keyboard they
 * use. This is the primary source; the dcAI keyboard and the chat-notification listener stay
 * as complements. It runs only while the parent grants the "layar" scope, the child sees dcAI
 * in Android's accessibility list, and the "dcAI aktif" notification stays visible: there is
 * no hidden mode.
 *
 * What leaves the phone is the same as every other source: [MessageIngest] masks the text
 * here, and only the masked text leaves. In online mode every masked message is sent for the
 * server to judge; in on-device mode the message is judged on the phone and only flagged ones
 * are sent. When a conversation is already risky, a screenshot is judged on the phone through
 * the existing vision pipeline; the screenshot is never sent.
 */
class ScreenReaderService : AccessibilityService() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private val screen = ScreenText()
    private var lastShot = 0L

    // Notification text (title and the sensitive-image nudge) in the dcAI app language, not
    // the phone's, like GuardianService and SiteGuardVpn.
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(dev.eziedutech.dcai.guardian.ui.localizedService(newBase))
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        event ?: return
        val store = ServiceLocator.store(this)
        if (store.config?.has("layar") != true) return
        val pkg = event.packageName?.toString() ?: return
        if (pkg == packageName || ScreenText.isNoiseApp(pkg)) return

        val root = rootInActiveWindow ?: return
        val collected = collect(root)
        val thread = collected.title ?: pkg
        RecentThreads.note(pkg, thread)

        // Outgoing: the child's own typing, taken when the field is cleared on send. This is
        // what the dcAI keyboard alone cannot give: it works with any keyboard.
        screen.onEditable(pkg, collected.editable.orEmpty())?.let { sent ->
            submit(thread, pkg, sender = "child", raw = sent)
        }

        // Incoming/transcript: only when a compose field is on screen (a messaging surface),
        // to keep ordinary app chrome out. New visible lines, minus the field's own text.
        if (collected.editable != null) {
            val field = collected.editable.trim()
            val lines = collected.lines.filter { it.trim() != field }
            for (line in screen.newLines(pkg, thread, lines)) {
                submit(thread, pkg, sender = "contact", raw = line)
            }
            maybeScreenshot(pkg, thread, collected.images)
        }
    }

    private fun submit(thread: String, pkg: String, sender: String, raw: String) {
        val ingest = ServiceLocator.ingest(this) ?: return
        scope.launch {
            runCatching {
                ingest.submit(
                    threadId = thread,
                    appPackage = pkg,
                    channel = "dm",
                    contactKnown = false,
                    sender = sender,
                    rawText = raw,
                )
            }.onFailure { Log.d(TAG, "screen submit failed: ${it.javaClass.simpleName}") }
        }
    }

    /**
     * One text buffer the child is editing, the other text lines on screen, a title, and where
     * the pictures are.
     */
    private class Collected(
        val editable: String?,
        val lines: List<String>,
        val title: String?,
        val images: List<ScreenBox>,
    )

    private fun collect(root: AccessibilityNodeInfo): Collected {
        var editable: String? = null
        val lines = ArrayList<String>()
        val images = ArrayList<ScreenBox>()
        val rect = Rect()
        val stack = ArrayDeque<AccessibilityNodeInfo>()
        stack.addLast(root)
        var budget = 600
        while (stack.isNotEmpty() && budget-- > 0) {
            val node = stack.removeLast()
            val t = node.text?.toString()?.trim()
            if (!t.isNullOrEmpty()) {
                if (node.isEditable) {
                    if (editable == null) editable = t
                } else {
                    lines.add(t)
                }
            }
            if (node.className?.toString()?.endsWith("ImageView") == true && node.isVisibleToUser) {
                node.getBoundsInScreen(rect)
                images.add(ScreenBox(rect.left, rect.top, rect.right, rect.bottom))
            }
            for (i in 0 until node.childCount) node.getChild(i)?.let { stack.addLast(it) }
        }
        val title = root.paneTitle?.toString()?.trim()?.takeIf { it.isNotEmpty() }
        return Collected(editable, lines, title, images)
    }

    /**
     * In a conversation already at perhatian or above, judge a screenshot on the phone through
     * the same vision pipeline the chat-SDK path uses. The bitmap never leaves the phone and is
     * recycled straight after. Each picture on screen is cut out and judged on its own (see
     * [ScreenImages]); with none, the whole screen is judged. A sensitive result shows the
     * child a reminder.
     */
    private fun maybeScreenshot(pkg: String, thread: String, images: List<ScreenBox>) {
        val store = ServiceLocator.store(this)
        if (store.config?.has("gambar") != true) return
        if (!ThreadLevels.atLeast(threadKey(pkg, thread), "perhatian")) return
        val now = SystemClock.elapsedRealtime()
        if (now - lastShot < SHOT_INTERVAL_MS) return
        lastShot = now
        takeScreenshot(
            Display.DEFAULT_DISPLAY,
            mainExecutor,
            object : TakeScreenshotCallback {
                override fun onSuccess(result: ScreenshotResult) {
                    val bitmap = toBitmap(result)
                    if (bitmap == null) return
                    scope.launch {
                        try {
                            val guard = ServiceLocator.imageGuard(this@ScreenReaderService) ?: return@launch
                            val context = ImageContext(Trigger.PERCAKAPAN, thread, pkg, "dm", "contact", false)
                            val boxes = ScreenImages.pick(images, bitmap.width, bitmap.height)
                            val sensitive = if (boxes.isEmpty()) {
                                guard.check(bitmap, context).blurAll
                            } else {
                                boxes.any { b ->
                                    val crop = Bitmap.createBitmap(bitmap, b.left, b.top, b.width, b.height)
                                    try {
                                        guard.check(crop, context).blurAll
                                    } finally {
                                        if (crop !== bitmap) crop.recycle()
                                    }
                                }
                            }
                            if (sensitive) {
                                Notifications.showNudge(
                                    this@ScreenReaderService,
                                    getString(R.string.screen_sensitive_nudge),
                                )
                            }
                        } catch (e: Exception) {
                            // Type only. An image check never takes the screen reader down.
                            Log.w(TAG, "screenshot check failed: ${e.javaClass.simpleName}")
                        } finally {
                            bitmap.recycle()
                        }
                    }
                }

                override fun onFailure(errorCode: Int) {
                    Log.d(TAG, "screenshot failed: $errorCode")
                }
            },
        )
    }

    /** A screenshot result into a software bitmap the detectors can read; buffer is closed. */
    private fun toBitmap(result: ScreenshotResult): Bitmap? {
        val buffer = result.hardwareBuffer
        return try {
            val hardware = Bitmap.wrapHardwareBuffer(buffer, result.colorSpace) ?: return null
            val software = hardware.copy(Bitmap.Config.ARGB_8888, false)
            hardware.recycle()
            software
        } catch (e: Exception) {
            Log.d(TAG, "screenshot decode failed: ${e.javaClass.simpleName}")
            null
        } finally {
            buffer.close()
        }
    }

    override fun onInterrupt() {}

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    companion object {
        private const val TAG = "dcai.screen"
        private const val SHOT_INTERVAL_MS = 15_000L

        /** Whether the parent turned on the dcAI accessibility service in Android's settings. */
        fun enabled(context: Context): Boolean {
            val flat = Settings.Secure.getString(
                context.contentResolver,
                Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES,
            ) ?: return false
            val me = ComponentName(context, ScreenReaderService::class.java)
            return flat.split(":").any { ComponentName.unflattenFromString(it) == me }
        }
    }
}
