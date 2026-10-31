"use client";

import { useT } from "@/lib/i18n";
import type { Level } from "@/lib/types";
import { LevelBadge, PageIntro, ReadNext, SiteFooter, SiteHeader } from "./ui";

type Section = { h: string; p?: string[]; list?: string[] };

/** One document section in a glass card, the same on every page. */
function Card({ s }: { s: Section }) {
  return (
    <section className="glass rounded-3xl p-7 sm:p-8">
      <h2 className="text-[1.3rem] font-bold">{s.h}</h2>
      {s.p?.map((para) => (
        <p key={para} className="mt-3 max-w-[66ch]">
          {para}
        </p>
      ))}
      {s.list && (
        <ul className="mt-3 max-w-[66ch] list-disc space-y-1.5 pl-5">
          {s.list.map((li) => (
            <li key={li}>{li}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

function Prose({ eyebrow, title, lead, sections, current }: { eyebrow: string; title: string; lead: string; sections: Section[]; current: "/privasi" }) {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-5xl px-5 pt-14 sm:px-8">
        <PageIntro eyebrow={eyebrow} title={title} lead={lead} />
        <div className="mt-10 grid gap-6">
          {sections.map((s) => (
            <Card key={s.h} s={s} />
          ))}
        </div>
        <ReadNext current={current} />
      </main>
      <SiteFooter />
    </>
  );
}

const PRIVACY: Record<"id" | "en", { title: string; lead: string; sections: Section[] }> = {
  id: {
    title: "Privasi",
    lead: "dcAI memberi orang tua pemahaman tentang pola percakapan anak. Isi percakapan tidak dibagikan. Halaman ini menjelaskan apa yang diproses, di mana, dan berapa lama.",
    sections: [
      {
        h: "Di ponsel anak",
        list: [
          "Pesan yang dibaca dcAI di ponsel anak, di aplikasi apa pun, lewat papan ketik dcAI, atau dari notifikasi obrolan, disamarkan di ponsel. Nama, nomor telepon, email, nomor kartu, alamat, dan sekolah diganti penanda sebelum apa pun dikirim.",
          "Hanya pesan yang ditandai berisiko yang dikirim ke server, dalam bentuk tersamarkan.",
          "Gambar dinilai di ponsel dan tidak pernah dikirim. Wajah dan data pribadi pada gambar yang akan dibagikan dikaburkan. Gambar sensitif dikaburkan penuh bila model deteksinya terpasang; model itu belum ada di versi ini.",
          "Anak selalu melihat notifikasi tetap selama dcAI aktif. Tidak ada mode tersembunyi.",
        ],
      },
      {
        h: "Di server dan model AI",
        list: [
          "Pesan tersamarkan diproses di memori untuk menilai pola, lalu dibuang. Isi pesan tidak disimpan di database atau di log.",
          "Model yang dipakai: Muse Spark dari Meta (lewat Meta Model API dan Fireworks) dan Llama dari Meta (lewat penyedia inferensi model terbuka). Yang dikirim ke model selalu sudah disamarkan.",
          "Tanya dcAI mengirim data dasbor anak Anda ke Muse Spark dengan nama anak diganti alias. Pertanyaan dan jawaban tidak disimpan.",
        ],
      },
      {
        h: "Berbagi dengan sekolah (opsional)",
        list: [
          "Hanya aktif bila orang tua menyetujui lingkup Ringkasan sekolah dan memasukkan kode kelas dari guru.",
          "Sekolah hanya melihat angka agregat per level untuk satu kelas, tidak pernah identitas, level, insight, atau percakapan satu anak pun.",
          "Angka baru muncul bila cukup anak ikut, demi menjaga anonimitas. Orang tua bisa keluar dari kelas kapan saja, dan anak langsung gugur dari hitungan.",
        ],
      },
      {
        h: "Yang disimpan",
        list: [
          "Skor, level, jenis pola, tingkat keyakinan, dan penjelasan untuk orang tua.",
          "Peristiwa, misalnya level naik atau perlindungan dimatikan.",
          "Insight, saran, dan pengingat yang sudah diterima anak.",
          "Nama aplikasi tempat percakapan terjadi, dan label gambar (bukan gambarnya).",
          "Untuk level mendesak, kutipan tersamarkan disimpan terenkripsi dan dihapus otomatis setelah 14 hari.",
          "Konfirmasi salah deteksi dari orang tua disimpan tanpa identitas anak, ponsel, atau gambar.",
        ],
      },
      {
        h: "Kendali orang tua",
        list: [
          "Setiap lingkup persetujuan bisa ditarik kapan saja, dan ponsel berhenti memakainya.",
          "Ponsel bisa dilepas dari dasbor; tokennya langsung berhenti berlaku.",
          "Keikutsertaan di kelas sekolah bisa dihentikan kapan saja dari Pengaturan.",
          "Semua data anak bisa dihapus dari Pengaturan. Catatan audit hanya menyimpan bahwa penghapusan terjadi, tanpa nama.",
        ],
      },
      {
        h: "Status MVP",
        p: [
          "dcAI adalah MVP hackathon dan belum dipakai oleh keluarga sungguhan. Semua data contoh adalah sintetis. Saat memakai kredit gratis, Meta dapat memakai isi permintaan untuk peningkatan produk, jadi hanya data sintetis yang dikirim. Teks persetujuan dan halaman ini belum ditinjau penasihat hukum.",
        ],
      },
    ],
  },
  en: {
    title: "Privacy",
    lead: "dcAI gives parents understanding of their child's conversation patterns. The conversations themselves are not shared. This page explains what is processed, where, and for how long.",
    sections: [
      {
        h: "On the child's phone",
        list: [
          "Messages dcAI reads on the child's phone, in any app, with the dcAI keyboard, or from chat notifications, are masked on the phone. Names, phone numbers, emails, card numbers, addresses and schools become markers before anything is sent.",
          "Only messages flagged as risky are sent to the server, masked.",
          "Images are judged on the phone and never sent. Faces and personal data in an image about to be shared are blurred. Sensitive images are fully blurred once a detection model is installed; this version has none yet.",
          "The child always sees a persistent notification while dcAI is on. There is no hidden mode.",
        ],
      },
      {
        h: "On the server and in AI models",
        list: [
          "Masked messages are processed in memory to assess patterns, then dropped. Message text is not stored in the database or in logs.",
          "Models used: Muse Spark by Meta (through the Meta Model API and Fireworks) and Llama by Meta (through an open-weights inference provider). What reaches a model is always masked first.",
          "Ask dcAI sends your child's dashboard data to Muse Spark with the child's name replaced by an alias. Questions and answers are not stored.",
        ],
      },
      {
        h: "Sharing with a school (optional)",
        list: [
          "Active only when a parent grants the School overview scope and enters the class code from the teacher.",
          "A school sees only aggregate counts per level for one class, never a single child's identity, level, insight or conversation.",
          "Numbers appear only when enough children take part, to keep it anonymous. A parent can leave a class at any time, and the child drops out of the counts at once.",
        ],
      },
      {
        h: "What is stored",
        list: [
          "Score, level, pattern types, confidence and the explanation for the parent.",
          "Events, such as a level rising or protection being turned off.",
          "Insight, advice and the reminders the child received.",
          "The name of the app where a chat happened, and image labels (not the images).",
          "For the urgent level, masked excerpts are stored encrypted and deleted automatically after 14 days.",
          "A parent's confirmation of a wrong detection is stored without the child, the phone or the image.",
        ],
      },
      {
        h: "Parent controls",
        list: [
          "Each consent scope can be withdrawn at any time, and the phone stops using it.",
          "A phone can be unpaired from the dashboard; its token stops working at once.",
          "Taking part in a school class can be stopped at any time from Settings.",
          "All of a child's data can be deleted from Settings. The audit log keeps only that a deletion happened, without names.",
        ],
      },
      {
        h: "MVP status",
        p: [
          "dcAI is a hackathon MVP and is not yet used by real families. All example data is synthetic. With free credits, Meta may use request content for product improvement, so only synthetic data is sent. The consent text and this page have not had legal review.",
        ],
      },
    ],
  },
};

export function PrivacyPage() {
  const { lang, t } = useT();
  return <Prose eyebrow={t("page.privacy.eyebrow")} current="/privasi" {...PRIVACY[lang]} />;
}

const HOW: Record<"id" | "en", { title: string; lead: string; levels: Record<Level, string>; sections: Section[] }> = {
  id: {
    title: "Cara AI membantu",
    lead: "Halaman ini bisa dibaca bersama anak. Isinya apa yang dibantu AI, apa yang tidak, dan kapan orang tua diberi tahu.",
    levels: {
      aman: "Obrolan biasa. Tidak ada yang dikirim ke orang tua.",
      perhatian: "Ada tanda awal. Anak mendapat pengingat; orang tua melihat insight di dasbor.",
      waspada: "Ada pola berisiko. Orang tua mendapat insight dan saran untuk bicara hari ini.",
      mendesak: "Pola berisiko tinggi, misalnya permintaan rahasia bersama ajakan pindah aplikasi. Orang tua diminta mendampingi anak sekarang.",
    },
    sections: [
      {
        h: "Yang dibantu AI",
        list: [
          "Mengenali pola lintas pesan. Satu pesan jarang cukup; yang dinilai adalah rangkaian, misalnya pujian berlebihan, lalu hadiah, lalu permintaan rahasia.",
          "Mengingatkan anak dengan kalimat singkat yang tidak menyalahkan, dan memberi satu langkah yang jelas.",
          "Memberi orang tua penjelasan dan pembuka percakapan.",
        ],
      },
      {
        h: "Yang tidak dilakukan AI",
        list: [
          "Tidak mengirim isi pesan ke orang tua.",
          "Tidak menyimpan gambar atau riwayat penjelajahan.",
          "Tidak membaca isi aplikasi lain. Untuk waktu online, yang dihitung hanya durasi per kategori.",
          "Tidak bekerja diam-diam. Anak selalu tahu dcAI aktif.",
        ],
      },
      {
        h: "Aturan di bawah AI",
        p: [
          "Ada aturan tetap yang tidak bisa diturunkan oleh model. Contohnya, orang yang belum dikenal meminta data pribadi berarti minimal waspada. Bila model sedang tidak tersedia, level tidak pernah ditampilkan sebagai aman.",
          "Setiap penilaian AI adalah perkiraan dan bisa salah. Bila gambar keliru dikaburkan, anak bisa menunjukkannya ke orang tua, dan orang tua yang memutuskan.",
        ],
      },
    ],
  },
  en: {
    title: "How the AI helps",
    lead: "This page can be read together with the child. It explains what the AI helps with, what it does not do, and when parents are told.",
    levels: {
      aman: "An ordinary chat. Nothing is sent to the parent.",
      perhatian: "An early sign. The child gets a reminder; the parent sees insight in the dashboard.",
      waspada: "A risky pattern. The parent gets insight and advice to talk today.",
      mendesak: "A high-risk pattern, such as secrecy together with a move to another app. The parent is asked to be with the child now.",
    },
    sections: [
      {
        h: "What the AI helps with",
        list: [
          "Recognising patterns across messages. One message is rarely enough; what counts is the sequence, such as heavy praise, then gifts, then a request for secrecy.",
          "Reminding the child in short sentences that never blame, with one clear step.",
          "Giving parents an explanation and conversation starters.",
        ],
      },
      {
        h: "What the AI does not do",
        list: [
          "It does not send message text to parents.",
          "It does not store images or browsing history.",
          "It does not read other apps. For time online, only the duration per category is counted.",
          "It does not work in secret. The child always knows dcAI is on.",
        ],
      },
      {
        h: "Rules under the AI",
        p: [
          "Fixed rules sit under the model and cannot be lowered by it. For example, a stranger asking for personal data means at least alert. When the model is unavailable, the level is never shown as safe.",
          "Every AI assessment is an estimate and can be wrong. If an image is blurred by mistake, the child can show it to a parent, and the parent decides.",
        ],
      },
    ],
  },
};

export function HowPage() {
  const { lang, t } = useT();
  const c = HOW[lang];
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-5xl px-5 pt-14 sm:px-8">
        <PageIntro eyebrow={t("page.how.eyebrow")} title={c.title} lead={c.lead} />
        <dl className="glass mt-10 divide-y divide-ink/[0.07] rounded-3xl px-7">
          {(Object.keys(c.levels) as Level[]).map((l) => (
            <div key={l} className="grid gap-2 py-5 sm:grid-cols-[12rem_1fr]">
              <dt>
                <LevelBadge level={l} />
              </dt>
              <dd>{c.levels[l]}</dd>
            </div>
          ))}
        </dl>
        <div className="mt-6 grid gap-6">
          {c.sections.map((s) => (
            <Card key={s.h} s={s} />
          ))}
        </div>
        <ReadNext current="/cara-kerja" />
      </main>
      <SiteFooter />
    </>
  );
}

/** A plain document page: header, then glass cards. Used for the guide and the terms. */
function DocPage({ eyebrow, title, lead, sections }: { eyebrow: string; title: string; lead: string; sections: Section[] }) {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-5xl px-5 pt-14 sm:px-8">
        <PageIntro eyebrow={eyebrow} title={title} lead={lead} />
        <div className="mt-10 grid gap-6">
          {sections.map((s) => (
            <Card key={s.h} s={s} />
          ))}
        </div>
      </main>
      <SiteFooter />
    </>
  );
}

const CONTACT = "zia@eziedutech.dev";

const GUIDE: Record<"id" | "en", { title: string; lead: string; sections: Section[] }> = {
  id: {
    title: "Panduan penggunaan",
    lead: "Langkah memakai dcAI, dari membuat akun sampai membaca dasbor. Semua di bawah persetujuan Anda, dan dcAI selalu terlihat di ponsel anak.",
    sections: [
      { h: "1. Buat akun orang tua", list: ["Daftar lewat halaman Daftar dengan email dan kata sandi. Bahasa bisa diubah kapan saja di Pengaturan umum."] },
      { h: "2. Tambah anak", list: ["Di dasbor, pilih Tambah anak. Isi nama panggilan (bisa diganti nanti di tab Pengaturan anak) dan rentang usia (10-12, 13-15, atau 16-17)."] },
      { h: "3. Setujui lingkup", list: ["Pilih apa yang boleh dibantu dcAI: percakapan, teks layar, gambar, situs, papan ketik, waktu online, dan opsional sekolah. Setiap lingkup bisa ditarik kapan saja di tab Pengaturan anak."] },
      { h: "4. Pasang ponsel anak", list: ["Buka tab Ponsel pada anak itu, pilih Hubungkan ponsel untuk membuat kode sekali pakai, lalu masukkan kode itu di aplikasi dcAI di ponsel anak.", "Saat memasang, buat PIN orang tua di ponsel. PIN dipakai untuk mematikan proteksi atau menyetujui situs/gambar, dan hanya tersimpan di ponsel itu.", "Anak uninstall atau ganti ponsel? Buat kode baru dari tab Ponsel dan pasang lagi."] },
      { h: "5. Baca dasbor", list: ["Ringkasan: level 7 hari terakhir, insight dengan pembuka percakapan, peristiwa, dan daftar percakapan (pola saja, tanpa isi pesan.)", "Waktu online: batas harian per kategori, jam tidur, jeda video pendek, dan mode fokus.", "Sekolah: masukkan kode kelas dari guru untuk ikut statistik kelas anonim, atau keluar kapan saja.", "Pengaturan: ganti nama anak, atur lingkup persetujuan, bersihkan riwayat, atau hapus semua data anak."] },
      { h: "6. Tanya dcAI", list: ["Tanyakan apa saja tentang insight anak Anda. Jawaban hanya dari data yang juga tampil di dasbor; pertanyaan dan jawaban tidak disimpan."] },
      { h: "Butuh bantuan?", p: [`Hubungi kami di ${CONTACT}.`] },
    ],
  },
  en: {
    title: "User guide",
    lead: "How to use dcAI, from creating an account to reading the dashboard. Everything runs under your consent, and dcAI is always visible on the child's phone.",
    sections: [
      { h: "1. Create a parent account", list: ["Sign up on the Sign up page with an email and a password. You can change the language any time in General settings."] },
      { h: "2. Add a child", list: ["In the dashboard, choose Add a child. Enter a nickname (you can rename it later in the child's Settings tab) and an age range (10-12, 13-15 or 16-17)."] },
      { h: "3. Agree to scopes", list: ["Choose what dcAI may help with: conversations, screen text, images, sites, the keyboard, time online, and optionally school. Each scope can be withdrawn at any time in the child's Settings tab."] },
      { h: "4. Pair the child's phone", list: ["Open that child's Phone tab, choose Connect a phone to make a single-use code, then enter it in the dcAI app on the child's phone.", "During setup, create a parent PIN on the phone. The PIN is used to turn protections off or to allow a site or image, and it is stored only on that phone.", "Child uninstalled or changed phones? Make a new code from the Phone tab and pair again."] },
      { h: "5. Read the dashboard", list: ["Overview: the level over the last 7 days, insight with conversation starters, events, and the conversation list (patterns only, never message text).", "Time online: daily limits per category, bedtime, short-video breaks, and focus mode.", "School: enter a class code from the teacher to join the anonymous class statistics, or leave at any time.", "Settings: rename the child, manage consent scopes, clear history, or delete all of the child's data."] },
      { h: "6. Ask dcAI", list: ["Ask anything about your child's insight. Answers come only from data the dashboard also shows; questions and answers are not stored."] },
      { h: "Need help?", p: [`Reach us at ${CONTACT}.`] },
    ],
  },
};

export function GuidePage() {
  const { lang, t } = useT();
  return <DocPage eyebrow={t("page.guide.eyebrow")} {...GUIDE[lang]} />;
}

const TERMS: Record<"id" | "en", { title: string; lead: string; sections: Section[] }> = {
  id: {
    title: "Ketentuan Layanan",
    lead: "Ketentuan penggunaan dcAI. Ini produk tahap awal (MVP) dan belum ditinjau penasihat hukum.",
    sections: [
      { h: "Tentang layanan", p: ["dcAI adalah layanan pendamping keselamatan digital anak, salah satu pilar digitalsafe.app oleh EZI EDUTECH. Saat ini berstatus MVP untuk peragaan dan pengembangan; semua data contoh adalah sintetis dan layanan belum ditujukan untuk keluarga sungguhan."] },
      { h: "Penggunaan yang diizinkan", list: ["Gunakan dcAI hanya untuk mendampingi anak Anda sendiri atau anak di bawah perwalian sah Anda.", "Selama MVP, jangan memasukkan data pribadi anak yang sebenarnya.", "Jangan menyalahgunakan layanan untuk mengawasi orang lain tanpa hak, atau melanggar hukum yang berlaku."] },
      { h: "Akun dan keamanan", list: ["Anda bertanggung jawab menjaga kerahasiaan kata sandi akun dan PIN orang tua.", "Beri tahu kami bila Anda menduga ada akses tanpa izin. Anda dapat keluar dari semua perangkat dari Pengaturan umum."] },
      { h: "Penilaian AI adalah perkiraan", p: ["Penilaian dan bimbingan dcAI dibuat oleh model AI, bisa salah, dan bukan nasihat medis, psikologis, atau hukum. Keputusan tetap pada Anda sebagai orang tua."] },
      { h: "Ketersediaan dan perubahan", p: ["Karena masih MVP, fitur dapat berubah, terganggu, atau dihentikan sewaktu-waktu tanpa pemberitahuan. Ketentuan ini dapat diperbarui; versi terbaru yang berlaku."] },
      { h: "Batasan tanggung jawab", p: ["Sejauh diizinkan hukum, layanan disediakan apa adanya tanpa jaminan apa pun, dan kami tidak bertanggung jawab atas kerugian yang timbul dari penggunaan MVP ini."] },
      { h: "Kode sumber", p: ["Kode dcAI tersedia dengan lisensi MIT. Komponen pihak ketiga mengikuti lisensinya masing-masing."] },
      { h: "Kontak", p: [`Pertanyaan tentang ketentuan ini dapat dikirim ke ${CONTACT}. Teks ini dan halaman Privasi belum ditinjau penasihat hukum.`] },
    ],
  },
  en: {
    title: "Terms of Service",
    lead: "The terms for using dcAI. This is an early-stage product (MVP) and has not had legal review.",
    sections: [
      { h: "About the service", p: ["dcAI is a child digital-safety companion, one pillar of digitalsafe.app by EZI EDUTECH. It is currently an MVP for demonstration and development; all example data is synthetic and the service is not yet meant for real families."] },
      { h: "Permitted use", list: ["Use dcAI only to support your own child or a child under your lawful guardianship.", "During the MVP, do not enter a real child's personal data.", "Do not misuse the service to watch other people without the right to, or to break applicable law."] },
      { h: "Account and security", list: ["You are responsible for keeping your account password and the parent PIN confidential.", "Tell us if you suspect unauthorised access. You can sign out of every device from General settings."] },
      { h: "AI assessments are estimates", p: ["dcAI's assessments and guidance are produced by AI models, can be wrong, and are not medical, psychological or legal advice. Decisions remain yours as the parent."] },
      { h: "Availability and changes", p: ["As an MVP, features may change, break or stop at any time without notice. These terms may be updated; the latest version applies."] },
      { h: "Limitation of liability", p: ["To the extent permitted by law, the service is provided as is, without warranty of any kind, and we are not liable for losses arising from use of this MVP."] },
      { h: "Source code", p: ["dcAI's code is available under the MIT license. Third-party components follow their own licenses."] },
      { h: "Contact", p: [`Questions about these terms can be sent to ${CONTACT}. This page and the Privacy page have not had legal review.`] },
    ],
  },
};

export function TermsPage() {
  const { lang, t } = useT();
  return <DocPage eyebrow={t("page.terms.eyebrow")} {...TERMS[lang]} />;
}
