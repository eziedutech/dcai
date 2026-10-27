"use client";

import { useT } from "@/lib/i18n";
import type { Level } from "@/lib/types";
import { LevelBadge, SiteFooter, SiteHeader } from "./ui";

type Section = { h: string; p?: string[]; list?: string[] };

function Prose({ title, lead, sections }: { title: string; lead: string; sections: Section[] }) {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-5 pt-10 sm:px-8">
        <h1 className="text-[2.2rem] font-extrabold leading-tight tracking-[-0.025em]">{title}</h1>
        <p className="mt-4 max-w-[62ch] text-lg text-slate">{lead}</p>
        {sections.map((s) => (
          <section key={s.h} className="mt-12">
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
        ))}
      </main>
      <SiteFooter />
    </>
  );
}

const PRIVACY: Record<"id" | "en", { title: string; lead: string; sections: Section[] }> = {
  id: {
    title: "Privasi",
    lead: "dcAI dirancang agar orang tua menerima pemahaman, bukan isi percakapan. Halaman ini menjelaskan apa yang diproses, di mana, dan berapa lama.",
    sections: [
      {
        h: "Di ponsel anak",
        list: [
          "Teks di layar dibaca dan disamarkan di ponsel. Nama, nomor telepon, email, nomor kartu, alamat, dan sekolah diganti penanda sebelum apa pun dikirim.",
          "Hanya pesan yang ditandai berisiko yang dikirim ke server, dalam bentuk tersamarkan.",
          "Gambar dinilai di ponsel. Gambar yang terdeteksi sensitif dikaburkan penuh dan tidak pernah dikirim.",
          "Anak selalu melihat notifikasi tetap selama dcAI aktif. Tidak ada mode tersembunyi.",
        ],
      },
      {
        h: "Di server dan model AI",
        list: [
          "Pesan tersamarkan diproses di memori untuk menilai pola, lalu dibuang. Isi pesan tidak disimpan di database atau di log.",
          "Model yang dipakai: Muse Spark dari Meta (lewat Meta Model API dan Fireworks) dan Llama dari Meta (lewat W&B Inference). Yang dikirim ke model selalu sudah disamarkan.",
          "Tanya dcAI mengirim data dasbor anak Anda ke Muse Spark dengan nama anak diganti alias. Pertanyaan dan jawaban tidak disimpan.",
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
          "Semua data anak bisa dihapus dari Pengaturan. Catatan audit hanya menyimpan bahwa penghapusan terjadi, tanpa nama.",
        ],
      },
      {
        h: "Status prototipe",
        p: [
          "dcAI masih prototipe untuk hackathon dan belum dipakai oleh keluarga sungguhan. Semua data contoh adalah sintetis. Saat memakai kredit gratis, Meta dapat memakai isi permintaan untuk peningkatan produk, jadi hanya data sintetis yang dikirim. Teks persetujuan dan halaman ini belum ditinjau penasihat hukum.",
        ],
      },
    ],
  },
  en: {
    title: "Privacy",
    lead: "dcAI is designed so parents receive understanding, not conversations. This page explains what is processed, where, and for how long.",
    sections: [
      {
        h: "On the child's phone",
        list: [
          "Screen text is read and masked on the phone. Names, phone numbers, emails, card numbers, addresses and schools become markers before anything is sent.",
          "Only messages flagged as risky are sent to the server, masked.",
          "Images are judged on the phone. An image detected as sensitive is fully blurred and never sent.",
          "The child always sees a persistent notification while dcAI is on. There is no hidden mode.",
        ],
      },
      {
        h: "On the server and in AI models",
        list: [
          "Masked messages are processed in memory to assess patterns, then dropped. Message text is not stored in the database or in logs.",
          "Models used: Muse Spark by Meta (through the Meta Model API and Fireworks) and Llama by Meta (through W&B Inference). What reaches a model is always masked first.",
          "Ask dcAI sends your child's dashboard data to Muse Spark with the child's name replaced by an alias. Questions and answers are not stored.",
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
          "All of a child's data can be deleted from Settings. The audit log keeps only that a deletion happened, without names.",
        ],
      },
      {
        h: "Prototype status",
        p: [
          "dcAI is a hackathon prototype and is not yet used by real families. All example data is synthetic. With free credits, Meta may use request content for product improvement, so only synthetic data is sent. The consent text and this page have not had legal review.",
        ],
      },
    ],
  },
};

export function PrivacyPage() {
  const { lang } = useT();
  return <Prose {...PRIVACY[lang]} />;
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
          "Mengenali pola, bukan kata. Satu pesan jarang cukup; yang dinilai adalah rangkaian, misalnya pujian berlebihan, lalu hadiah, lalu permintaan rahasia.",
          "Mengingatkan anak dengan kalimat singkat yang tidak menyalahkan, dan memberi satu langkah yang jelas.",
          "Memberi orang tua penjelasan dan pembuka percakapan, bukan perintah untuk menghukum.",
        ],
      },
      {
        h: "Yang tidak dilakukan AI",
        list: [
          "Tidak mengirim isi pesan ke orang tua.",
          "Tidak menyimpan gambar, rekaman suara, atau riwayat penjelajahan.",
          "Tidak memblokir aplikasi atau mengatur waktu layar. Itu tugas Family Link.",
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
          "Recognising patterns, not words. One message is rarely enough; what counts is the sequence, such as heavy praise, then gifts, then a request for secrecy.",
          "Reminding the child in short sentences that never blame, with one clear step.",
          "Giving parents an explanation and conversation starters, never instructions to punish.",
        ],
      },
      {
        h: "What the AI does not do",
        list: [
          "It does not send message text to parents.",
          "It does not store images, voice recordings or browsing history.",
          "It does not block apps or set screen time. That is Family Link's job.",
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
  const { lang } = useT();
  const c = HOW[lang];
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-5 pt-10 sm:px-8">
        <h1 className="text-[2.2rem] font-extrabold leading-tight tracking-[-0.025em]">{c.title}</h1>
        <p className="mt-4 max-w-[62ch] text-lg text-slate">{c.lead}</p>
        <dl className="mt-10 divide-y divide-line border-y border-line">
          {(Object.keys(c.levels) as Level[]).map((l) => (
            <div key={l} className="grid gap-2 py-4 sm:grid-cols-[12rem_1fr]">
              <dt>
                <LevelBadge level={l} />
              </dt>
              <dd>{c.levels[l]}</dd>
            </div>
          ))}
        </dl>
        {c.sections.map((s) => (
          <section key={s.h} className="mt-12">
            <h2 className="text-[1.3rem] font-bold">{s.h}</h2>
            {s.p?.map((para) => (
              <p key={para} className="mt-3 max-w-[66ch]">{para}</p>
            ))}
            {s.list && (
              <ul className="mt-3 max-w-[66ch] list-disc space-y-1.5 pl-5">
                {s.list.map((li) => (
                  <li key={li}>{li}</li>
                ))}
              </ul>
            )}
          </section>
        ))}
      </main>
      <SiteFooter />
    </>
  );
}
