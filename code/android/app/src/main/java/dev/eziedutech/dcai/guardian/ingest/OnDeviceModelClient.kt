package dev.eziedutech.dcai.guardian.ingest

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.os.IBinder
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

/**
 * The main process's handle on the :ondevice model service. It binds on demand and runs one
 * prompt, awaiting the result over the AIDL callback. If the model process is killed (out of
 * memory), the binder dies: the awaiting call is failed (or times out, see the caller), the
 * service reference is dropped, and the next call rebinds a fresh process. The caller treats any
 * failure as "model declined" and sends the message online, so nothing here can crash dcAI.
 */
class OnDeviceModelClient(context: Context) {
    private val appContext = context.applicationContext
    private val bindLock = Mutex()

    @Volatile private var service: IOnDeviceModel? = null
    private var connection: ServiceConnection? = null

    private suspend fun bound(): IOnDeviceModel {
        service?.let { return it }
        return bindLock.withLock {
            service?.let { return it }
            suspendCancellableCoroutine { cont ->
                val conn = object : ServiceConnection {
                    override fun onServiceConnected(name: ComponentName?, binder: IBinder?) {
                        val svc = IOnDeviceModel.Stub.asInterface(binder)
                        service = svc
                        if (cont.isActive) cont.resume(svc)
                    }

                    override fun onServiceDisconnected(name: ComponentName?) {
                        // The :ondevice process died (likely out of memory); force a rebind.
                        service = null
                    }
                }
                connection = conn
                val intent = Intent(appContext, OnDeviceModelService::class.java)
                val ok = appContext.bindService(intent, conn, Context.BIND_AUTO_CREATE)
                if (!ok && cont.isActive) {
                    cont.resumeWithException(IllegalStateException("bind failed"))
                }
            }
        }
    }

    /** Run one prompt in the :ondevice process and return the generated text. Throws if the
     * model declines or its process dies; the caller maps that to the online fallback. */
    suspend fun generate(prompt: String): String {
        val svc = bound()
        return suspendCancellableCoroutine { cont ->
            val callback = object : IOnDeviceCallback.Stub() {
                override fun onResult(text: String?) {
                    if (cont.isActive) cont.resume(text.orEmpty())
                }

                override fun onError(reason: String?) {
                    if (cont.isActive) cont.resumeWithException(RuntimeException(reason ?: "error"))
                }
            }
            try {
                svc.generate(prompt, callback)
            } catch (t: Throwable) {
                // Binder likely dead: drop the reference so the next call rebinds.
                service = null
                if (cont.isActive) cont.resumeWithException(t)
            }
        }
    }
}
