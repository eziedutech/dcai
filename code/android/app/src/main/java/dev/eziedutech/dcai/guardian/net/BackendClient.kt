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

    suspend fun sendSiteSignal(signal: SiteSignalRequest): Unit = withContext(Dispatchers.IO) {
        executeNoBody(authed(Request.Builder().url(url("/v1/device/sites/signals"))).post(body(signal)).build())
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
                onEvent(LiveEvent(type ?: "message", obj))
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
