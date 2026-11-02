package dev.eziedutech.dcai.guardian.net

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.sse.EventSource
import okhttp3.sse.EventSourceListener
import okhttp3.sse.EventSources
import java.util.concurrent.TimeUnit

/** The device is no longer paired (parent revoked it, or the child's data was erased). */
class DeviceRevokedException : Exception("device not paired")

class BackendException(val code: Int, message: String) : Exception(message)

/** For logs: the error type, or the HTTP status of a server answer. Never the message,
 * which may echo a request detail. */
fun Throwable.brief(): String = when (this) {
    is BackendException -> "http $code"
    // The coroutine library's own wording ("Job was cancelled") and the cause's type.
    is kotlinx.coroutines.CancellationException -> "cancelled (${message?.take(60)}; cause ${cause?.javaClass?.simpleName})"
    else -> javaClass.simpleName
}

/**
 * Talks to the dcAI backend as the child's phone. Every call carries the device token,
 * except pairing. Masking happens before text is passed here (see ingest), so what leaves
 * the phone over this client is already masked.
 */
class BackendClient(
    private val baseUrl: String,
    private val tokenProvider: () -> String?,
) {
    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }
    private val jsonMedia = "application/json; charset=utf-8".toMediaType()
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()
    // SSE must never time out while idle; heartbeats keep it alive.
    private val sseClient = client.newBuilder().readTimeout(0, TimeUnit.SECONDS).build()

    private fun url(path: String) = baseUrl.trimEnd('/') + path

    private fun authed(builder: Request.Builder): Request.Builder {
        tokenProvider()?.let { builder.header("Authorization", "Bearer $it") }
        return builder
    }

    private inline fun <reified T> body(value: T) =
        json.encodeToString(value).toRequestBody(jsonMedia)

    private inline fun <reified R> execute(request: Request): R = client.newCall(request).execute().use { resp ->
        val text = resp.body.string()
        if (resp.code == 401) throw DeviceRevokedException()
        if (!resp.isSuccessful) throw BackendException(resp.code, "HTTP ${resp.code}")
        json.decodeFromString<R>(text)
    }

    suspend fun pair(code: String, deviceName: String, appVersion: String): PairResponse =
        withContext(Dispatchers.IO) {
            val req = Request.Builder()
                .url(url("/v1/device/pair"))
                .post(body(PairRequest(code = code, deviceName = deviceName, appVersion = appVersion)))
                .build()
            execute<PairResponse>(req)
        }

    /** The current consent text; public, no token needed. */
    suspend fun consentText(): ConsentText = withContext(Dispatchers.IO) {
        execute<ConsentText>(Request.Builder().url(url("/v1/consents/text")).get().build())
    }

    suspend fun config(): DeviceConfig = withContext(Dispatchers.IO) {
        execute<DeviceConfig>(authed(Request.Builder().url(url("/v1/device/config"))).get().build())
    }

    suspend fun heartbeat(appVersion: String, services: Map<String, Boolean>): DeviceConfig =
        withContext(Dispatchers.IO) {
            val req = authed(Request.Builder().url(url("/v1/device/heartbeat")))
                .post(body(HeartbeatRequest(appVersion, services))).build()
            execute<DeviceConfig>(req)
        }

    suspend fun sendMessage(message: DeviceMessageRequest, wait: Boolean = false): DeviceMessageResponse =
        withContext(Dispatchers.IO) {
            val suffix = if (wait) "?wait=true" else ""
            val req = authed(Request.Builder().url(url("/v1/device/messages$suffix")))
                .post(body(message)).build()
            execute<DeviceMessageResponse>(req)
        }

    suspend fun sendImageSignal(signal: ImageSignalRequest): Unit = withContext(Dispatchers.IO) {
        executeNoBody(authed(Request.Builder().url(url("/v1/device/images"))).post(body(signal)).build())
    }

    suspend fun sendDetectionFeedback(feedback: DetectionFeedbackRequest): Unit = withContext(Dispatchers.IO) {
        executeNoBody(authed(Request.Builder().url(url("/v1/device/detection-feedback"))).post(body(feedback)).build())
    }

    suspend fun siteManifest(): SiteManifest = withContext(Dispatchers.IO) {
        execute<SiteManifest>(authed(Request.Builder().url(url("/v1/device/sites"))).get().build())
    }

    /** Streams one category list into [target]. The caller checks the hash. */
    suspend fun downloadSiteList(name: String, target: java.io.File): Unit = withContext(Dispatchers.IO) {
        val req = authed(Request.Builder().url(url("/v1/device/sites/$name"))).get().build()
        client.newCall(req).execute().use { resp ->
            if (resp.code == 401) throw DeviceRevokedException()
            if (!resp.isSuccessful) throw BackendException(resp.code, "HTTP ${resp.code}")
            target.outputStream().use { out -> resp.body.byteStream().copyTo(out) }
        }
    }

    /** The on-device stage 1 model manifest (sizes and sha256), to decide whether to download. */
    suspend fun stage1Manifest(): Stage1Manifest = withContext(Dispatchers.IO) {
        execute<Stage1Manifest>(
            authed(Request.Builder().url(url("/v1/device/model/stage1/manifest"))).get().build()
        )
    }

    /**
     * Streams a model file to [target], resuming from whatever is already there with a Range
     * request so a dropped 2 GB download continues instead of starting over. [onProgress] gets
     * (bytes so far, total) as it runs. The caller verifies the sha256 afterwards.
     */
    suspend fun downloadModelFile(
        path: String,
        target: java.io.File,
        totalBytes: Long,
        onProgress: (Long, Long) -> Unit,
    ): Unit = withContext(Dispatchers.IO) {
        val have = if (target.exists()) target.length() else 0L
        if (have >= totalBytes && totalBytes > 0) {
            onProgress(totalBytes, totalBytes)
            return@withContext
        }
        val builder = authed(Request.Builder().url(url(path))).get()
        if (have > 0) builder.header("Range", "bytes=$have-")
        val request = builder.build()
        client.newCall(request).execute().use { resp ->
            if (resp.code == 401) throw DeviceRevokedException()
            if (!resp.isSuccessful) throw BackendException(resp.code, "HTTP ${resp.code}")
            // 200 means the server ignored the Range (or there was nothing yet): start over.
            val append = resp.code == 206 && have > 0
            var done = if (append) have else 0L
            java.io.FileOutputStream(target, append).use { out ->
                val buf = ByteArray(1 shl 16)
                resp.body.byteStream().use { input ->
                    while (true) {
                        val n = input.read(buf)
                        if (n < 0) break
                        out.write(buf, 0, n)
                        done += n
                        onProgress(done, totalBytes)
                    }
                }
            }
        }
    }

    suspend fun sendSiteSignal(signal: SiteSignalRequest): Unit = withContext(Dispatchers.IO) {
        executeNoBody(authed(Request.Builder().url(url("/v1/device/sites/signals"))).post(body(signal)).build())
    }

    suspend fun sendUsage(usage: UsageRequest): Unit = withContext(Dispatchers.IO) {
        executeNoBody(authed(Request.Builder().url(url("/v1/device/usage"))).post(body(usage)).build())
    }

    suspend fun requestTime(request: TimeRequestBody): TimeRequestOut = withContext(Dispatchers.IO) {
        execute<TimeRequestOut>(authed(Request.Builder().url(url("/v1/device/time-requests"))).post(body(request)).build())
    }

    suspend fun myTimeRequests(): List<TimeRequestOut> = withContext(Dispatchers.IO) {
        execute<List<TimeRequestOut>>(authed(Request.Builder().url(url("/v1/device/time-requests"))).get().build())
    }

    private fun executeNoBody(request: Request) = client.newCall(request).execute().use { resp ->
        if (resp.code == 401) throw DeviceRevokedException()
        if (!resp.isSuccessful) throw BackendException(resp.code, "HTTP ${resp.code}")
    }

    /** Opens the live stream. onEvent runs on OkHttp's thread; hop to your own scope. */
    fun openStream(lastEventId: String?, onEvent: (LiveEvent) -> Unit, onClosed: (Int?) -> Unit): EventSource {
        val builder = authed(Request.Builder().url(url("/v1/device/stream")).header("Accept", "text/event-stream"))
        lastEventId?.let { builder.header("Last-Event-ID", it) }
        val listener = object : EventSourceListener() {
            override fun onEvent(eventSource: EventSource, id: String?, type: String?, data: String) {
                val obj = runCatching { json.parseToJsonElement(data).jsonObject }.getOrNull() ?: return
                onEvent(LiveEvent(type ?: "message", obj, id))
            }

            override fun onFailure(eventSource: EventSource, t: Throwable?, response: okhttp3.Response?) {
                onClosed(response?.code)
            }

            override fun onClosed(eventSource: EventSource) = onClosed(null)
        }
        return EventSources.createFactory(sseClient).newEventSource(builder.build(), listener)
    }

    fun cancelAll() {
        client.dispatcher.cancelAll()
    }
}
