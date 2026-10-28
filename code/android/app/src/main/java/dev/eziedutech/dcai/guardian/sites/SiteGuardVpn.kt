package dev.eziedutech.dcai.guardian.sites

import android.content.Context
import android.content.Intent
import android.net.ConnectivityManager
import android.net.VpnService
import android.os.ParcelFileDescriptor
import android.util.Log
import dev.eziedutech.dcai.guardian.ServiceLocator
import dev.eziedutech.dcai.guardian.net.SiteSignalRequest
import dev.eziedutech.dcai.guardian.service.Notifications
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import java.io.FileInputStream
import java.io.FileOutputStream
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.Inet4Address
import java.net.InetAddress
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.Executors

/**
 * Site protection as a DNS-only VPN. The phone's DNS server is set to an address inside the
 * VPN, and only that address is routed into it: app traffic itself never passes through
 * dcAI. Each looked-up name is matched on the phone against the category lists. A listed
 * site gets "no such domain" and the child is told why; any other name is forwarded to the
 * network's own resolver and answered as usual.
 *
 * Nothing about a lookup is stored or sent. A held site sends its category to the server,
 * at most once per category in a while. The VPN key icon shows in the status bar the whole
 * time, and the child can see the protection on dcAI's screen.
 */
class SiteGuardVpn : VpnService() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var tun: ParcelFileDescriptor? = null
    @Volatile private var matcher: SiteMatcher? = null
    private val forwarders = Executors.newFixedThreadPool(4)
    private val lastSignal = ConcurrentHashMap<String, Long>()
    private val lastNotice = ConcurrentHashMap<String, Long>()

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            stop()
            return START_NOT_STICKY
        }
        if (intent?.action == ACTION_RELOAD) {
            scope.launch { reload(sync = false) }
            return START_STICKY
        }
        if (tun == null) start()
        return START_STICKY
    }

    private fun start() {
        val store = ServiceLocator.store(this)
        if (!store.isPaired || store.config?.has("domain") != true) {
            stopSelf()
            return
        }
        // The network's resolvers, read before the VPN becomes the default network.
        val upstream = upstreamDns()
        val builder = Builder()
            .setSession("dcAI")
            .addAddress(VPN_ADDRESS, 32)
            .addDnsServer(DNS_ADDRESS)
            .addRoute(DNS_ADDRESS, 32)
            .setBlocking(true)
        // dcAI's own traffic (the backend, the forwarded lookups) stays outside the VPN.
        runCatching { builder.addDisallowedApplication(packageName) }
        val iface = builder.establish() ?: run {
            stopSelf()
            return
        }
        tun = iface
        running = true
        scope.launch { reload(sync = true) }
        Thread({ loop(iface, upstream) }, "dcai-dns").start()
    }

    private suspend fun reload(sync: Boolean) {
        val client = ServiceLocator.client(this) ?: return
        val lists = SiteLists(this, client)
        if (sync) lists.sync()
        matcher = SiteMatcher(lists.load(), ServiceLocator.store(this).allowedSites)
    }

    private fun loop(iface: ParcelFileDescriptor, upstream: List<InetAddress>) {
        val input = FileInputStream(iface.fileDescriptor)
        val output = FileOutputStream(iface.fileDescriptor)
        val buffer = ByteArray(32767)
        try {
            while (running) {
                val n = input.read(buffer)
                if (n <= 0) continue
                val query = DnsQuery.parse(buffer, n) ?: continue
                val match = matcher?.match(query.name)
                if (match != null) {
                    write(output, query.nxdomain())
                    held(match)
                } else {
                    forwarders.execute { forward(query, upstream, output) }
                }
            }
        } catch (e: Exception) {
            // Type only: a message could name a site.
            if (running) Log.d(TAG, "dns loop ended: ${e.javaClass.simpleName}")
        }
    }

    private fun forward(query: DnsQuery, upstream: List<InetAddress>, output: FileOutputStream) {
        for (server in upstream) {
            try {
                DatagramSocket().use { socket ->
                    protect(socket)
                    socket.soTimeout = 4000
                    val dns = query.dns
                    socket.send(DatagramPacket(dns, dns.size, server, 53))
                    val reply = ByteArray(4096)
                    val packet = DatagramPacket(reply, reply.size)
                    socket.receive(packet)
                    write(output, query.reply(reply.copyOf(packet.length)))
                    return
                }
            } catch (_: Exception) {
                // Try the next resolver; the app retries on its own if all fail.
            }
        }
    }

    @Synchronized
    private fun write(output: FileOutputStream, packet: ByteArray) {
        runCatching { output.write(packet) }
    }

    private fun held(match: SiteMatch) {
        val now = System.currentTimeMillis()
        // One page asks for many names; tell the child once per site in a few minutes.
        if (now - (lastNotice[match.listed] ?: 0L) > NOTICE_MS) {
            lastNotice[match.listed] = now
            Notifications.showSiteHeld(this, match)
        }
        if (now - (lastSignal[match.category] ?: 0L) > SIGNAL_MS) {
            lastSignal[match.category] = now
            scope.launch {
                val client = ServiceLocator.client(this@SiteGuardVpn) ?: return@launch
                val version = SiteLists(this@SiteGuardVpn, client).manifest()?.version ?: return@launch
                runCatching { client.sendSiteSignal(SiteSignalRequest(match.category, version)) }
                    .onFailure { Log.d(TAG, "site signal failed: ${it.javaClass.simpleName}") }
            }
        }
    }

    private fun upstreamDns(): List<InetAddress> {
        val cm = getSystemService(ConnectivityManager::class.java)
        val servers = cm.activeNetwork?.let { cm.getLinkProperties(it)?.dnsServers }.orEmpty()
            .filterIsInstance<Inet4Address>()
            .filter { it.hostAddress != DNS_ADDRESS }
        // Without a network resolver there is nothing to forward to but a public one.
        return servers.ifEmpty { listOf(InetAddress.getByName(FALLBACK_DNS)) }
    }

    private fun stop() {
        running = false
        runCatching { tun?.close() }
        tun = null
        stopSelf()
    }

    override fun onRevoke() {
        // The VPN was switched off in the phone's settings; the heartbeat tells the parent.
        stop()
        super.onRevoke()
    }

    override fun onDestroy() {
        running = false
        runCatching { tun?.close() }
        scope.cancel()
        forwarders.shutdownNow()
        super.onDestroy()
    }

    companion object {
        private const val TAG = "dcai.sites"
        private const val VPN_ADDRESS = "10.111.222.2"
        private const val DNS_ADDRESS = "10.111.222.1"
        private const val FALLBACK_DNS = "1.1.1.1"
        private const val NOTICE_MS = 5 * 60_000L
        private const val SIGNAL_MS = 30 * 60_000L
        const val ACTION_STOP = "dev.eziedutech.dcai.guardian.sites.STOP"
        const val ACTION_RELOAD = "dev.eziedutech.dcai.guardian.sites.RELOAD"

        @Volatile var running = false
            private set

        fun start(context: Context) {
            context.startService(Intent(context, SiteGuardVpn::class.java))
        }

        fun reload(context: Context) {
            if (running) context.startService(Intent(context, SiteGuardVpn::class.java).setAction(ACTION_RELOAD))
        }

        fun stop(context: Context) {
            context.startService(Intent(context, SiteGuardVpn::class.java).setAction(ACTION_STOP))
        }
    }
}
