"use client";

import { useT } from "@/lib/i18n";
import { DevicesScene } from "./illustrations";
import { PageIntro, SiteFooter, SiteHeader } from "./ui";

// The roadmap page. It describes plans, not shipped features, and names no product or company,
// only operating systems and their own frameworks. Bilingual copy lives inline, like the other
// document pages.

type Group = { h: string; items: string[] };
type Platform = { tag: string; title: string; lead: string; groups: Group[] };
type Matrix = { cols: string[]; rows: { feature: string; cells: string[] }[] };
type Content = {
  title: string;
  lead: string;
  planned: string;
  intro: string;
  platforms: Platform[];
  matrixTitle: string;
  matrix: Matrix;
  closeTitle: string;
  close: string[];
};

const COPY: Record<"id" | "en", Content> = {
  id: {
    title: "Next Plan for dcAI",
    lead: "dcAI hari ini adalah aplikasi Android di ponsel anak. Langkah berikutnya membawa mesin yang sama, penyamaran di perangkat, alur model, daftar situs, dan dasbor orang tua serta sekolah, ke komputer yang dipakai di lab sekolah, komputer bersama, dan laptop milik siswa (BYOD), untuk keselamatan sehari-hari sekaligus mode ujian untuk praktik dan penilaian.",
    planned: "Rancangan, belum dibangun. Halaman ini menjelaskan arah berikutnya, bukan fitur yang sudah ada.",
    intro: "Setiap platform berbicara ke backend yang sama lewat REST dan SSE yang sama, jadi orang tua dan sekolah tetap memakai satu dasbor. Prinsip privasi dcAI ikut dibawa: penyamaran di perangkat di semua platform, dcAI selalu terlihat, tanpa mode tersembunyi, dan mode ujian selalu eksplisit serta dibatasi waktu.",
    platforms: [
      {
        tag: "Windows",
        title: "Kiosk dan Safety Guardian",
        lead: "Untuk lab sekolah, komputer umum, dan laptop pribadi siswa, Windows perlu penegakan di tingkat sistem.",
        groups: [
          {
            h: "Reset sesi otomatis",
            items: [
              "Partisi sistem dijaga tetap bersih: perubahan sistem, pemasangan berkas, program jahat, dan jejak selama sesi siswa dihapus otomatis saat komputer dinyalakan ulang.",
              "Satu area terpisah tetap bisa ditulis, khusus untuk cache lokal dcAI, token pairing, dan antrean pesan luring.",
            ],
          },
          {
            h: "Mode ujian dan penilaian",
            items: [
              "Kiosk ketat: menonaktifkan perpindahan antar jendela, tombol sistem, pengelola tugas, dan pusat notifikasi lewat kebijakan Windows.",
              "Penjaga multi-monitor: mematikan layar kedua atau melarang berbagi layar saat mode ujian aktif.",
              "Pemblokir papan klip dan tangkapan layar supaya soal tidak bisa disalin atau difoto layar.",
            ],
          },
          {
            h: "Filter situs dan aplikasi tingkat sistem",
            items: [
              "Filter di lapisan jaringan lewat Windows Filtering Platform (WFP): memblokir situs berbahaya dari mesin daftar situs yang sudah ada (5,1 juta+ domain), lepas dari browser apa pun yang dipakai siswa.",
              "Batas durasi aplikasi desktop lewat pelacakan jendela depan (Win32), dengan batas harian dan jam tidur yang sama seperti versi Android.",
            ],
          },
          {
            h: "Pembacaan teks di perangkat",
            items: [
              "Ekstraksi ketikan secara lokal lewat kait masukan Windows, lalu aturan penyamaran yang sama persis dengan versi Android dan server sebelum teks apa pun sampai ke model.",
            ],
          },
          {
            h: "Arsitektur",
            items: [
              "Layanan latar belakang native berjalan dengan hak SYSTEM: mengurus filter jaringan, kebijakan sistem, dan status reset sesi. Tidak bisa dihentikan siswa tanpa akses administrator atau PIN orang tua/guru.",
              "Klien kiosk berjalan di sesi siswa: menampilkan indikator proteksi, layar istirahat, pengingat halus, dan antarmuka mode ujian.",
            ],
          },
        ],
      },
      {
        tag: "iOS, iPadOS dan macOS",
        title: "Integrasi native yang mengutamakan privasi",
        lead: "Apple membatasi pembacaan lintas aplikasi secara ketat, jadi dcAI memakai kerangka resmi yang disediakan sistem operasinya.",
        groups: [
          {
            h: "iOS dan iPadOS",
            items: [
              "Family Controls dan Screen Time (DeviceActivity, ManagedSettings): batas waktu aplikasi, pemblokiran kategori, dan mode fokus atau ujian secara resmi, tanpa akal-akalan.",
              "Konfigurasi perisai: layar istirahat khas dcAI saat batas waktu habis atau aplikasi dibatasi.",
              "Filter konten lewat Network Extension (Content Filter Provider): pencocokan hash domain di tingkat sistem untuk Safari maupun browser lain, tanpa meloloskan isi pesan ke server.",
              "Ekstensi papan ketik dcAI: analisis ketikan dengan penyamaran di perangkat yang identik dengan Android.",
            ],
          },
          {
            h: "macOS",
            items: [
              "Endpoint Security dan ekstensi sistem: mengawasi peluncuran aplikasi dan mencegah daemon dcAI dimatikan tanpa otorisasi admin atau PIN.",
              "Screen Time API: menyelaraskan batas waktu dan mode fokus antara iOS dan macOS.",
              "Mode ujian lewat Automatic Assessment Configuration: saat aktif, sistem operasi secara native memblokir perekaman layar, berbagi layar, asisten suara, notifikasi, dan aplikasi lain.",
            ],
          },
        ],
      },
    ],
    matrixTitle: "Matriks lintas platform",
    matrix: {
      cols: ["Modul", "Android (sekarang)", "Windows", "iOS", "macOS"],
      rows: [
        { feature: "Penyamaran masukan", cells: ["SDK aplikasi dan papan ketik", "Layanan desktop dan kait masukan", "Ekstensi papan ketik", "Aksesibilitas dan ekstensi aplikasi"] },
        { feature: "Filter situs", cells: ["VPN DNS lokal", "Filter jaringan sistem (WFP)", "Filter Network Extension", "Filter Network Extension"] },
        { feature: "Durasi dan batas waktu", cells: ["Akses penggunaan", "Pelacakan jendela depan (Win32)", "Screen Time (DeviceActivity)", "Screen Time dan Endpoint Security"] },
        { feature: "Kunci dan ujian", cells: ["Kiosk dan penguncian tugas", "Kebijakan dan kiosk Windows", "Akses Terpandu dan mode penilaian", "Automatic Assessment Configuration"] },
        { feature: "Reset sesi", cells: ["tidak ada", "Filter disk sistem", "tidak ada (OS tersandbox)", "Profil terbatas"] },
        { feature: "Sinkronisasi orang tua/sekolah", cells: ["SSE dan REST", "SSE dan REST", "SSE dan REST", "SSE dan REST"] },
      ],
    },
    closeTitle: "Satu backend, satu dasbor",
    close: [
      "Apa pun platformnya, orang tua dan sekolah tetap melihat gambaran yang sama di dasbor yang sama, karena semua perangkat berbicara ke backend yang sama.",
      "Peran orang tua dan sekolah tidak berubah: orang tua tetap wali yang mengendalikan persetujuan, dan sekolah tetap hanya melihat angka agregat anonim per kelas.",
    ],
  },
  en: {
    title: "Next Plan for dcAI",
    lead: "Today dcAI is an Android app on a child's phone. The next step takes the same engine, on-device masking, the model pipeline, the site lists and the parent and school dashboards, to the computers used in school labs, shared machines and students' own laptops (BYOD), for everyday safety and for an exam mode for practicals and tests.",
    planned: "A plan, not built yet. This page describes the next direction, not shipped features.",
    intro: "Every platform talks to the same backend over the same REST and SSE, so the parent and the school keep one dashboard. dcAI's privacy stance carries over: on-device masking everywhere, dcAI always visible, no hidden mode, and an exam mode that is always explicit and time-boxed.",
    platforms: [
      {
        tag: "Windows",
        title: "Kiosk and Safety Guardian",
        lead: "For school labs, shared computers and students' own laptops, Windows needs system-level enforcement.",
        groups: [
          {
            h: "Automatic session reset",
            items: [
              "The system partition is kept clean: system changes, installed files, malware and history during a student session are wiped automatically on restart.",
              "One separate area stays writable, for dcAI's own local cache, the pairing token and the offline message queue.",
            ],
          },
          {
            h: "Exam and assessment mode",
            items: [
              "A strict kiosk: it disables window switching, the system keys, the task manager and the notification centre through Windows policy.",
              "A multi-monitor guard: it turns off a second display or blocks screen sharing while exam mode is on.",
              "A clipboard and screenshot block, so exam content cannot be copied or captured.",
            ],
          },
          {
            h: "System-wide site and app filtering",
            items: [
              "Filtering at the network layer through the Windows Filtering Platform (WFP): it blocks harmful sites from the existing site-list engine (5.1 million+ domains), independent of any browser the student uses.",
              "Desktop app time limits through foreground-window tracking (Win32), with the same daily limits and bedtime as Android.",
            ],
          },
          {
            h: "On-device text reading",
            items: [
              "Typed text is read locally through Windows input hooks, then the exact same masking rules as the Android and server versions run before any text reaches the model.",
            ],
          },
          {
            h: "Architecture",
            items: [
              "A native background service runs as SYSTEM: it handles the network filter, system policy and the session-reset state. A student cannot stop it without administrator access or the parent or teacher PIN.",
              "A kiosk client runs in the student's session: protection indicators, the break screen, gentle nudges and the exam-mode interface.",
            ],
          },
        ],
      },
      {
        tag: "iOS, iPadOS and macOS",
        title: "Privacy-first native integration",
        lead: "Apple limits cross-app reading tightly, so dcAI uses the official frameworks its operating systems provide.",
        groups: [
          {
            h: "iOS and iPadOS",
            items: [
              "Family Controls and Screen Time (DeviceActivity, ManagedSettings): app time limits, category blocks and a focus or exam mode officially, with no workaround.",
              "A shield configuration: dcAI's own break screen when a limit is reached or an app is restricted.",
              "Content filtering through a Network Extension (Content Filter Provider): domain-hash matching at the system level for Safari and other browsers, without letting message content reach the server.",
              "A dcAI keyboard extension: typing analysis with the same on-device masking as Android.",
            ],
          },
          {
            h: "macOS",
            items: [
              "Endpoint Security and system extensions: see app launches and stop the dcAI daemon being killed without admin authorisation or the PIN.",
              "The Screen Time API: keep time limits and focus mode in step between iOS and macOS.",
              "Exam mode through Automatic Assessment Configuration: while it is on, the operating system natively blocks screen recording, screen sharing, the voice assistant, notifications and other apps.",
            ],
          },
        ],
      },
    ],
    matrixTitle: "Cross-platform matrix",
    matrix: {
      cols: ["Module", "Android (now)", "Windows", "iOS", "macOS"],
      rows: [
        { feature: "Ingest masking", cells: ["App SDK and keyboard", "Desktop service and input hooks", "Keyboard extension", "Accessibility and app extension"] },
        { feature: "Site filter", cells: ["Local DNS VPN", "System network filter (WFP)", "Network Extension filter", "Network Extension filter"] },
        { feature: "Usage and time limit", cells: ["Usage access", "Foreground-window tracking (Win32)", "Screen Time (DeviceActivity)", "Screen Time and Endpoint Security"] },
        { feature: "Lockdown and exams", cells: ["Kiosk and task locking", "Windows policy and kiosk", "Guided Access and assessment mode", "Automatic Assessment Configuration"] },
        { feature: "Session reset", cells: ["none", "System disk filter", "none (sandboxed OS)", "Restricted profiles"] },
        { feature: "Parent/school sync", cells: ["SSE and REST", "SSE and REST", "SSE and REST", "SSE and REST"] },
      ],
    },
    closeTitle: "One backend, one dashboard",
    close: [
      "Whatever the platform, the parent and the school see the same picture in the same dashboard, because every device talks to the same backend.",
      "The parent and school roles do not change: the parent stays the guardian who controls consent, and the school still sees only anonymous aggregate counts per class.",
    ],
  },
};

function PlatformBlock({ p }: { p: Platform }) {
  return (
    <section className="mt-12">
      <p className="eyebrow">{p.tag}</p>
      <h2 className="mt-2 text-[1.5rem] font-bold tracking-[-0.02em]">{p.title}</h2>
      <p className="mt-3 max-w-[66ch] text-slate">{p.lead}</p>
      <div className="mt-6 grid gap-5 md:grid-cols-2">
        {p.groups.map((g) => (
          <div key={g.h} className="glass rounded-3xl p-6 sm:p-7">
            <h3 className="font-bold">{g.h}</h3>
            <ul className="mt-3 space-y-2 text-[0.95rem] text-ink/80">
              {g.items.map((it) => (
                <li key={it} className="flex gap-2.5">
                  <span aria-hidden className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-navy/70" />
                  {it}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

export function NextPlanPage() {
  const { lang, t } = useT();
  const c = COPY[lang];
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-5xl px-5 pt-14 sm:px-8">
        <PageIntro eyebrow={t("home.next.eyebrow")} title={c.title} lead={c.lead} />

        <div className="mt-10">
          <DevicesScene className="mx-auto max-w-2xl" />
        </div>

        <p className="mt-8 flex items-start gap-2.5 rounded-2xl border border-dashed border-navy/25 bg-navy/[0.04] px-5 py-4 text-[0.95rem] font-medium text-ink/85">
          <span aria-hidden className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-navy/15 text-[0.7rem] font-bold text-navy">!</span>
          {c.planned}
        </p>

        <p className="mt-8 max-w-[70ch] text-lg text-ink/75">{c.intro}</p>

        {c.platforms.map((p) => (
          <PlatformBlock key={p.tag} p={p} />
        ))}

        <section className="mt-14">
          <h2 className="text-[1.5rem] font-bold tracking-[-0.02em]">{c.matrixTitle}</h2>
          <div className="glass mt-5 overflow-x-auto rounded-3xl p-2 sm:p-3">
            <table className="w-full border-collapse text-left text-[0.9rem]">
              <thead>
                <tr>
                  {c.matrix.cols.map((col, i) => (
                    <th
                      key={col}
                      className={`p-3 align-bottom text-[0.8rem] font-bold tracking-wide ${i === 0 ? "text-ink" : "text-navy"}`}
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {c.matrix.rows.map((row) => (
                  <tr key={row.feature} className="border-t border-ink/[0.08]">
                    <th scope="row" className="p-3 align-top font-semibold text-ink">{row.feature}</th>
                    {row.cells.map((cell, i) => (
                      <td key={i} className="p-3 align-top text-ink/75">{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="mt-14 mb-4">
          <h2 className="text-[1.5rem] font-bold tracking-[-0.02em]">{c.closeTitle}</h2>
          {c.close.map((para) => (
            <p key={para} className="mt-3 max-w-[70ch] text-slate">{para}</p>
          ))}
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
