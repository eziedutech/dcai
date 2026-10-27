"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { Lang } from "./types";

// Indonesian first. Words that frame the product as surveillance are not used anywhere.

const id = {
  "nav.how": "Cara kerja",
  "nav.privacy": "Privasi",
  "nav.signin": "Masuk",
  "nav.dashboard": "Dasbor",
  "nav.lang": "English",

  "home.title": "Anak dibimbing saat itu juga. Orang tua paham tanpa membaca obrolannya.",
  "home.lead":
    "dcAI Guardian dipasang orang tua di ponsel Android anak usia 10 sampai 17 tahun. Saat obrolan mulai mengikuti pola berisiko, anak mendapat pengingat singkat dengan alasannya. Orang tua menerima pola yang terlihat dan cara membicarakannya.",
  "home.cta": "Buka dasbor",
  "home.cta2": "Lihat apa yang disimpan",
  "home.demo.child": "Yang dilihat anak",
  "home.demo.parent": "Yang dilihat orang tua",
  "home.demo.msg1": "kamu jago banget mainnya, beda dari yang lain",
  "home.demo.msg2": "aku kasih skin gratis, tapi jangan bilang siapa-siapa ya",
  "home.demo.msg3": "kirim foto kamu dong, terus kita lanjut di aplikasi lain",
  "home.demo.contact": "Kontak baru di game",
  "home.demo.nudge":
    "Kamu boleh berhenti membalas. Permintaan foto dan rahasia dari orang yang baru dikenal adalah tanda untuk cerita ke orang dewasa yang kamu percaya.",
  "home.demo.patterns": "Pola yang terlihat",
  "home.demo.p1": "Meminta kerahasiaan",
  "home.demo.p2": "Menawarkan hadiah",
  "home.demo.p3": "Meminta foto",
  "home.demo.p4": "Mengajak pindah aplikasi",
  "home.demo.starter": "Pembuka percakapan",
  "home.demo.starterText": "Ada teman baru di game yang bikin kamu bingung akhir-akhir ini?",
  "home.demo.noText": "Isi pesan tidak dikirim ke orang tua dan tidak disimpan.",

  "home.layer.title": "Family Link untuk batas. dcAI untuk pemahaman.",
  "home.layer.lead":
    "Google Family Link mengatur aplikasi, waktu layar, pembelian, dan lokasi. dcAI bekerja di sampingnya: memahami apa yang terjadi di layar, lalu membimbing anak dan orang tua.",
  "home.layer.fl": "Family Link",
  "home.layer.dc": "dcAI Guardian",
  "home.layer.r1": "Menyetujui dan memblokir aplikasi",
  "home.layer.r2": "Waktu layar dan jadwal tidur",
  "home.layer.r3": "Mengenali pola pendekatan berisiko dalam obrolan",
  "home.layer.r4": "Pengingat untuk anak pada saat itu juga",
  "home.layer.r5": "Mengaburkan gambar sensitif di ponsel",
  "home.layer.r6": "Insight dan pembuka percakapan untuk orang tua",

  "home.steps.title": "Dari layar anak sampai saran untuk orang tua",
  "home.step1.t": "Di ponsel",
  "home.step1.b":
    "Teks di layar dibaca dan disamarkan di ponsel. Nama, nomor, alamat, dan sekolah diganti penanda. Gambar sensitif dikaburkan dan tidak pernah dikirim.",
  "home.step2.t": "Hanya yang ditandai",
  "home.step2.b":
    "Pesan yang terlihat berisiko dikirim dalam bentuk tersamarkan. Llama memberi label perilaku per pesan, aturan tetap menjaga batas bawah.",
  "home.step3.t": "Dinilai sebagai pola",
  "home.step3.b":
    "Muse Spark menilai pola di seluruh rangkaian pesan. Skor tidak pernah turun di bawah aturan keselamatan.",
  "home.step4.t": "Membimbing",
  "home.step4.b":
    "Anak mendapat pengingat paling banyak dua kalimat. Orang tua mendapat apa yang terlihat, mengapa penting, dan tiga pembuka percakapan.",

  "home.privacy.title": "Yang disimpan, dan yang tidak pernah disimpan",
  "home.privacy.stored": "Disimpan",
  "home.privacy.never": "Tidak pernah disimpan",
  "home.privacy.s1": "Skor dan level risiko",
  "home.privacy.s2": "Jenis pola perilaku",
  "home.privacy.s3": "Nama aplikasi tempat obrolan terjadi",
  "home.privacy.s4": "Label gambar, misalnya dikaburkan",
  "home.privacy.s5": "Insight dan saran untuk orang tua",
  "home.privacy.n1": "Isi pesan",
  "home.privacy.n2": "Gambar dan foto",
  "home.privacy.n3": "Rekaman suara",
  "home.privacy.n4": "Riwayat penjelajahan",
  "home.privacy.note":
    "Anak selalu tahu dcAI aktif: ada notifikasi tetap di ponselnya, dan tidak ada mode tersembunyi.",

  "home.meta.title": "Dibangun dengan model Meta",
  "home.meta.muse": "Muse Spark menilai pola percakapan, menulis bimbingan, dan menjawab pertanyaan orang tua lewat Tanya dcAI.",
  "home.meta.llama": "Llama memberi label perilaku per pesan sebagai penyaring awal.",
  "home.meta.next": "Rencana berikutnya: model Llama yang lebih kecil hasil distilasi, berjalan di ponsel.",
  "home.foot": "Prototipe untuk Meta Global AI Developer Hackathon 2026. Semua data contoh adalah sintetis.",

  "auth.signin": "Masuk",
  "auth.signup": "Daftar",
  "auth.email": "Email",
  "auth.password": "Kata sandi",
  "auth.name": "Nama Anda",
  "auth.passwordHint": "Minimal 10 karakter.",
  "auth.toSignup": "Belum punya akun? Daftar",
  "auth.toSignin": "Sudah punya akun? Masuk",
  "auth.wrong": "Email atau kata sandi tidak cocok.",
  "auth.taken": "Email ini sudah terdaftar. Masuk dengan email ini.",
  "auth.invalid": "Periksa lagi isian Anda.",
  "auth.signupTitle": "Buat akun orang tua",
  "auth.signinTitle": "Masuk ke dasbor",

  "dash.children": "Anak",
  "dash.addChild": "Tambah anak",
  "dash.ask": "Tanya dcAI",
  "dash.settings": "Pengaturan",
  "dash.signout": "Keluar",
  "dash.empty.title": "Mulai dengan menambahkan anak",
  "dash.empty.body":
    "Anda akan memilih apa yang boleh dibantu dcAI, lalu memasangkan ponsel anak dengan kode.",
  "dash.levelNow": "Level saat ini",
  "dash.window": "7 hari terakhir",
  "dash.estimate": "Penilaian AI adalah perkiraan dan bisa salah.",
  "dash.convActive": "percakapan dinilai",
  "dash.convAttention": "perlu didampingi",
  "dash.blurred": "gambar dikaburkan",
  "dash.protection": "Perlindungan di ponsel",
  "dash.protectionOn": "Aktif",
  "dash.protectionOff": "Mati",
  "dash.noDevice": "Belum ada ponsel yang dipasangkan.",
  "dash.pairNow": "Pasangkan ponsel",
  "dash.lastSeen": "Terakhir terhubung",
  "dash.latestInsight": "Insight terbaru",
  "dash.noInsight":
    "Belum ada insight. dcAI menulis insight saat level naik ke perlu perhatian atau lebih tinggi.",
  "dash.whatWeSee": "Yang terlihat",
  "dash.whyItMatters": "Mengapa penting",
  "dash.starters": "Pembuka percakapan",
  "dash.do": "Sebaiknya",
  "dash.dont": "Sebaiknya tidak",
  "dash.childWasTold": "Yang sudah disampaikan ke anak",
  "dash.lesson": "Pelajaran satu menit",
  "dash.help": "Kanal bantuan",
  "dash.template": "Dari templat yang sudah ditinjau",
  "dash.events": "Peristiwa",
  "dash.noEvents": "Belum ada peristiwa dalam 30 hari terakhir.",
  "dash.conversations": "Percakapan",
  "dash.noConversations": "Belum ada percakapan yang dinilai.",
  "dash.in": "di",
  "dash.live": "Terhubung langsung",
  "dash.offline": "Menyambung ulang",
  "dash.confidence": "Keyakinan",
  "dash.textNotStored": "Isi pesan tidak disimpan, jadi tidak bisa ditampilkan.",

  "add.title": "Tambah anak",
  "add.step1": "Profil",
  "add.step2": "Persetujuan",
  "add.step3": "Pasangkan ponsel",
  "add.nickname": "Nama panggilan",
  "add.nicknameHint": "Cukup nama panggilan. Tanggal lahir tidak diminta.",
  "add.age": "Rentang usia",
  "add.next": "Lanjut",
  "add.consentLead": "Baca teks ini, lalu pilih lingkup yang Anda setujui. Setiap lingkup bisa ditarik kapan saja.",
  "add.agree": "Setujui lingkup terpilih",
  "add.needScope": "Pilih minimal satu lingkup.",
  "add.pairLead":
    "Buka dcAI Guardian di ponsel anak dan masukkan kode ini. Kode hanya berlaku sekali dan sebentar.",
  "add.validUntil": "Berlaku sampai",
  "add.newCode": "Buat kode baru",
  "add.done": "Selesai, ke dasbor",
  "add.paired": "Ponsel terpasang",

  "ask.title": "Tanya dcAI",
  "ask.lead":
    "Tanyakan apa saja tentang insight anak Anda. Tanya dcAI hanya membaca data yang juga ada di dasbor ini, dan nama anak diganti alias sebelum dikirim ke model.",
  "ask.placeholder": "Misalnya: apa yang perlu saya bicarakan dengan anak minggu ini?",
  "ask.send": "Kirim",
  "ask.thinking": "Membaca insight",
  "ask.fallback": "Jawaban ini dibuat dari ringkasan tetap karena model sedang tidak tersedia.",
  "ask.used": "Data yang dibaca",
  "ask.notStored": "Pertanyaan dan jawaban tidak disimpan.",
  "ask.s1": "Apa yang terjadi minggu ini?",
  "ask.s2": "Bagaimana memulai obrolan tentang ini?",
  "ask.s3": "Apa yang dcAI simpan tentang anak saya?",
  "ask.tooMany": "Terlalu banyak pertanyaan. Coba lagi dalam satu menit.",

  "set.title": "Pengaturan",
  "set.language": "Bahasa",
  "set.languageHint": "Juga dipakai untuk bimbingan anak dan aplikasi di ponselnya.",
  "set.saved": "Tersimpan",
  "set.consent": "Lingkup persetujuan",
  "set.withdraw": "Tarik",
  "set.grant": "Setujui",
  "set.devices": "Ponsel",
  "set.revoke": "Lepaskan ponsel",
  "set.revoked": "Dilepas",
  "set.delete": "Hapus semua data anak",
  "set.deleteHint":
    "Profil, persetujuan, penilaian, insight, peristiwa, dan ponsel yang terpasang dihapus. Tidak bisa dibatalkan.",
  "set.deleteConfirm": "Ketik nama panggilan anak untuk menghapus",
  "set.deleteButton": "Hapus data",

  "level.aman": "Aman",
  "level.perhatian": "Perlu perhatian",
  "level.waspada": "Waspada",
  "level.mendesak": "Mendesak",
  "levelHint.aman": "Tidak ada pola yang perlu diperhatikan.",
  "levelHint.perhatian": "Ada tanda awal. Cukup diperhatikan dan diajak bicara santai.",
  "levelHint.waspada": "Ada pola berisiko. Bicarakan dengan anak hari ini.",
  "levelHint.mendesak": "Pola berisiko tinggi. Dampingi anak sekarang dan simpan bukti.",

  "pattern.membangun_kedekatan": "Membangun kedekatan dengan cepat",
  "pattern.meminta_kerahasiaan": "Meminta kerahasiaan",
  "pattern.pindah_kanal": "Mengajak pindah aplikasi",
  "pattern.meminta_data_pribadi": "Meminta data pribadi atau foto",
  "pattern.menawarkan_hadiah": "Menawarkan hadiah",
  "pattern.menguji_batas": "Menguji batas",
  "pattern.menekan_mengancam": "Menekan atau mengancam",

  "event.risiko_naik": "Level naik",
  "event.data_pribadi_dibagikan": "Anak membagikan data pribadi",
  "event.dukungan_dibutuhkan": "Anak butuh dukungan",
  "event.perlindungan_dimatikan": "Perlindungan dimatikan di ponsel",
  "event.perlindungan_aktif": "Perlindungan aktif kembali",
  "event.gambar_sensitif": "Gambar sensitif dikaburkan",
  "event.gambar_data_pribadi": "Gambar berisi data pribadi ditahan",

  "scope.percakapan": "Percakapan",
  "scope.gambar": "Gambar",
  "scope.domain": "Situs",
  "scope.suara": "Pesan suara",
  "scope.keyboard": "Papan ketik",
  "scopeHint.percakapan": "Pesan yang ditandai di ponsel dinilai polanya setelah disamarkan.",
  "scopeHint.gambar": "Gambar dinilai di ponsel; yang sensitif dikaburkan dan tidak dikirim.",
  "scopeHint.domain": "Situs dicocokkan dengan daftar di ponsel; hanya kategorinya dikirim.",
  "scopeHint.suara": "Pesan suara di obrolan berisiko diubah jadi teks, lalu disamarkan.",
  "scopeHint.keyboard": "Nada teks yang diketik diperiksa setelah disamarkan. Opsional.",

  "service.accessibility": "Pembaca layar dcAI",
  "service.notification": "Notifikasi tetap",
  "service.vpn": "Penyaring situs",
  "service.keyboard": "Papan ketik dcAI",

  "conf.rendah": "rendah",
  "conf.sedang": "sedang",
  "conf.tinggi": "tinggi",

  "common.loading": "Memuat",
  "common.error": "Gagal memuat. Periksa koneksi lalu muat ulang halaman.",
  "common.cancel": "Batal",
  "common.age": "tahun",
};

type Key = keyof typeof id;

const en: Record<Key, string> = {
  "nav.how": "How it works",
  "nav.privacy": "Privacy",
  "nav.signin": "Sign in",
  "nav.dashboard": "Dashboard",
  "nav.lang": "Bahasa Indonesia",

  "home.title": "Children get guidance in the moment. Parents understand without reading the chat.",
  "home.lead":
    "A parent installs dcAI Guardian on their child's Android phone, for ages 10 to 17. When a chat starts to follow a risky pattern, the child gets a short reminder with the reason. The parent receives the pattern and how to talk about it.",
  "home.cta": "Open the dashboard",
  "home.cta2": "See what is stored",
  "home.demo.child": "What the child sees",
  "home.demo.parent": "What the parent sees",
  "home.demo.msg1": "you're really good at this game, not like the others",
  "home.demo.msg2": "I'll give you a free skin, but don't tell anyone ok",
  "home.demo.msg3": "send me a photo of you, then let's move to another app",
  "home.demo.contact": "New contact in a game",
  "home.demo.nudge":
    "You can stop replying. A request for photos and secrecy from someone you just met is a sign to tell an adult you trust.",
  "home.demo.patterns": "Patterns seen",
  "home.demo.p1": "Asking for secrecy",
  "home.demo.p2": "Offering gifts",
  "home.demo.p3": "Asking for a photo",
  "home.demo.p4": "Moving to another app",
  "home.demo.starter": "Conversation starter",
  "home.demo.starterText": "Has a new friend in a game made you feel unsure lately?",
  "home.demo.noText": "Message text is not sent to the parent and is not stored.",

  "home.layer.title": "Family Link for limits. dcAI for understanding.",
  "home.layer.lead":
    "Google Family Link manages apps, screen time, purchases and location. dcAI works next to it: it understands what happens on screen, then guides the child and the parent.",
  "home.layer.fl": "Family Link",
  "home.layer.dc": "dcAI Guardian",
  "home.layer.r1": "Approve and block apps",
  "home.layer.r2": "Screen time and bedtime",
  "home.layer.r3": "Recognise risky approach patterns in chats",
  "home.layer.r4": "Reminders for the child in the moment",
  "home.layer.r5": "Blur sensitive images on the phone",
  "home.layer.r6": "Insight and conversation starters for parents",

  "home.steps.title": "From the child's screen to advice for the parent",
  "home.step1.t": "On the phone",
  "home.step1.b":
    "Screen text is read and masked on the phone. Names, numbers, addresses and schools become markers. Sensitive images are blurred and never sent.",
  "home.step2.t": "Only what is flagged",
  "home.step2.b":
    "Messages that look risky are sent masked. Llama labels behaviour per message, and fixed rules keep a floor under the score.",
  "home.step3.t": "Assessed as a pattern",
  "home.step3.b":
    "Muse Spark assesses the pattern across the whole sequence of messages. The score never drops below the safety rules.",
  "home.step4.t": "Guidance",
  "home.step4.b":
    "The child gets a reminder of at most two sentences. The parent gets what was seen, why it matters and three conversation starters.",

  "home.privacy.title": "What is stored, and what never is",
  "home.privacy.stored": "Stored",
  "home.privacy.never": "Never stored",
  "home.privacy.s1": "Risk score and level",
  "home.privacy.s2": "Types of behaviour pattern",
  "home.privacy.s3": "The app where a chat happened",
  "home.privacy.s4": "Image labels, such as blurred",
  "home.privacy.s5": "Insight and advice for the parent",
  "home.privacy.n1": "Message text",
  "home.privacy.n2": "Images and photos",
  "home.privacy.n3": "Voice recordings",
  "home.privacy.n4": "Browsing history",
  "home.privacy.note":
    "The child always knows dcAI is on: a persistent notification on their phone, and no hidden mode.",

  "home.meta.title": "Built with Meta models",
  "home.meta.muse": "Muse Spark assesses chat patterns, writes the guidance and answers parents through Ask dcAI.",
  "home.meta.llama": "Llama labels behaviour per message as the first filter.",
  "home.meta.next": "Next: a smaller distilled Llama model that runs on the phone.",
  "home.foot": "Prototype for the Meta Global AI Developer Hackathon 2026. All example data is synthetic.",

  "auth.signin": "Sign in",
  "auth.signup": "Sign up",
  "auth.email": "Email",
  "auth.password": "Password",
  "auth.name": "Your name",
  "auth.passwordHint": "At least 10 characters.",
  "auth.toSignup": "No account yet? Sign up",
  "auth.toSignin": "Have an account? Sign in",
  "auth.wrong": "Email or password does not match.",
  "auth.taken": "This email is already registered. Sign in with it.",
  "auth.invalid": "Check your entries.",
  "auth.signupTitle": "Create a parent account",
  "auth.signinTitle": "Sign in to the dashboard",

  "dash.children": "Children",
  "dash.addChild": "Add a child",
  "dash.ask": "Ask dcAI",
  "dash.settings": "Settings",
  "dash.signout": "Sign out",
  "dash.empty.title": "Start by adding a child",
  "dash.empty.body": "You will choose what dcAI may help with, then pair the child's phone with a code.",
  "dash.levelNow": "Current level",
  "dash.window": "Last 7 days",
  "dash.estimate": "AI assessments are estimates and can be wrong.",
  "dash.convActive": "chats assessed",
  "dash.convAttention": "need support",
  "dash.blurred": "images blurred",
  "dash.protection": "Protection on the phone",
  "dash.protectionOn": "On",
  "dash.protectionOff": "Off",
  "dash.noDevice": "No phone is paired yet.",
  "dash.pairNow": "Pair a phone",
  "dash.lastSeen": "Last connected",
  "dash.latestInsight": "Latest insight",
  "dash.noInsight": "No insight yet. dcAI writes one when the level rises to needs attention or higher.",
  "dash.whatWeSee": "What we see",
  "dash.whyItMatters": "Why it matters",
  "dash.starters": "Conversation starters",
  "dash.do": "Do",
  "dash.dont": "Avoid",
  "dash.childWasTold": "What the child was told",
  "dash.lesson": "One-minute lesson",
  "dash.help": "Help channels",
  "dash.template": "From a reviewed template",
  "dash.events": "Events",
  "dash.noEvents": "No events in the last 30 days.",
  "dash.conversations": "Conversations",
  "dash.noConversations": "No conversation has been assessed yet.",
  "dash.in": "in",
  "dash.live": "Live",
  "dash.offline": "Reconnecting",
  "dash.confidence": "Confidence",
  "dash.textNotStored": "Message text is not stored, so it cannot be shown.",

  "add.title": "Add a child",
  "add.step1": "Profile",
  "add.step2": "Consent",
  "add.step3": "Pair the phone",
  "add.nickname": "Nickname",
  "add.nicknameHint": "A nickname is enough. No date of birth is asked.",
  "add.age": "Age range",
  "add.next": "Continue",
  "add.consentLead": "Read this text, then choose the scopes you agree to. Each scope can be withdrawn at any time.",
  "add.agree": "Agree to the selected scopes",
  "add.needScope": "Choose at least one scope.",
  "add.pairLead": "Open dcAI Guardian on the child's phone and enter this code. It works once, for a few minutes.",
  "add.validUntil": "Valid until",
  "add.newCode": "Make a new code",
  "add.done": "Done, go to the dashboard",
  "add.paired": "Phone paired",

  "ask.title": "Ask dcAI",
  "ask.lead":
    "Ask anything about your child's insight. Ask dcAI reads only data that this dashboard also shows, and children's names are replaced by aliases before anything reaches the model.",
  "ask.placeholder": "For example: what should I talk about with my child this week?",
  "ask.send": "Send",
  "ask.thinking": "Reading the insight",
  "ask.fallback": "This answer is a fixed summary because the model is not available.",
  "ask.used": "Data read",
  "ask.notStored": "Questions and answers are not stored.",
  "ask.s1": "What happened this week?",
  "ask.s2": "How do I start a conversation about this?",
  "ask.s3": "What does dcAI store about my child?",
  "ask.tooMany": "Too many questions. Try again in a minute.",

  "set.title": "Settings",
  "set.language": "Language",
  "set.languageHint": "Also used for the child's guidance and the app on their phone.",
  "set.saved": "Saved",
  "set.consent": "Consent scopes",
  "set.withdraw": "Withdraw",
  "set.grant": "Agree",
  "set.devices": "Phones",
  "set.revoke": "Unpair phone",
  "set.revoked": "Unpaired",
  "set.delete": "Delete all of this child's data",
  "set.deleteHint":
    "The profile, consent, assessments, insight, events and paired phones are deleted. This cannot be undone.",
  "set.deleteConfirm": "Type the child's nickname to delete",
  "set.deleteButton": "Delete data",

  "level.aman": "Safe",
  "level.perhatian": "Needs attention",
  "level.waspada": "Alert",
  "level.mendesak": "Urgent",
  "levelHint.aman": "No pattern that needs attention.",
  "levelHint.perhatian": "An early sign. Keep an eye on it and talk casually.",
  "levelHint.waspada": "A risky pattern. Talk with your child today.",
  "levelHint.mendesak": "A high-risk pattern. Be with your child now and keep evidence.",

  "pattern.membangun_kedekatan": "Building closeness fast",
  "pattern.meminta_kerahasiaan": "Asking for secrecy",
  "pattern.pindah_kanal": "Moving to another app",
  "pattern.meminta_data_pribadi": "Asking for personal data or photos",
  "pattern.menawarkan_hadiah": "Offering gifts",
  "pattern.menguji_batas": "Testing limits",
  "pattern.menekan_mengancam": "Pressure or threats",

  "event.risiko_naik": "Level rose",
  "event.data_pribadi_dibagikan": "Child shared personal data",
  "event.dukungan_dibutuhkan": "Child needs support",
  "event.perlindungan_dimatikan": "Protection turned off on the phone",
  "event.perlindungan_aktif": "Protection back on",
  "event.gambar_sensitif": "Sensitive image blurred",
  "event.gambar_data_pribadi": "Image with personal data held back",

  "scope.percakapan": "Conversations",
  "scope.gambar": "Images",
  "scope.domain": "Sites",
  "scope.suara": "Voice notes",
  "scope.keyboard": "Keyboard",
  "scopeHint.percakapan": "Messages flagged on the phone are assessed as patterns after masking.",
  "scopeHint.gambar": "Images are judged on the phone; sensitive ones are blurred and never sent.",
  "scopeHint.domain": "Sites are matched against a list on the phone; only the category is sent.",
  "scopeHint.suara": "Voice notes in risky chats become text, then are masked.",
  "scopeHint.keyboard": "The tone of typed text is checked after masking. Optional.",

  "service.accessibility": "dcAI screen reader",
  "service.notification": "Persistent notification",
  "service.vpn": "Site filter",
  "service.keyboard": "dcAI keyboard",

  "conf.rendah": "low",
  "conf.sedang": "medium",
  "conf.tinggi": "high",

  "common.loading": "Loading",
  "common.error": "Could not load. Check the connection, then reload the page.",
  "common.cancel": "Cancel",
  "common.age": "years",
};

const DICTS: Record<Lang, Record<Key, string>> = { id, en };
export type TKey = Key;

type Ctx = { lang: Lang; setLang: (l: Lang) => void; t: (k: Key) => string; tx: (k: string, fallback?: string) => string };
const LangContext = createContext<Ctx | null>(null);

export function LangProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("id");
  useEffect(() => {
    const saved = localStorage.getItem("dcai_lang");
    // eslint-disable-next-line react-hooks/set-state-in-effect -- read once after hydration
    if (saved === "en" || saved === "id") setLangState(saved);
  }, []);
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);
  const setLang = useCallback((l: Lang) => {
    localStorage.setItem("dcai_lang", l);
    setLangState(l);
  }, []);
  const value = useMemo<Ctx>(() => {
    const dict = DICTS[lang];
    return {
      lang,
      setLang,
      t: (k) => dict[k],
      // For keys built from data (patterns, events): unknown values show as they are.
      tx: (k, fallback) => (dict as Record<string, string>)[k] ?? fallback ?? k,
    };
  }, [lang, setLang]);
  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
}

export function useT() {
  const ctx = useContext(LangContext);
  if (!ctx) throw new Error("useT outside LangProvider");
  return ctx;
}
