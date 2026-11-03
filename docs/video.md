# dcAI demo video: scenario and transcript

Target about 3 minutes (check the hackathon's duration limit). Synthetic data only on screen.

## Preparation

- Test phone: dcAI 0.3.9 paired to the demo account; Messenger Z installed; adb connected.
- Laptop: `/dasbor` open on the demo child; a `/sekolah` class with at least 5 consenting children.
- Clear the demo child's history first (Dashboard > Settings > Clear history).
- Never show personal chats, keys, `.env` or `credentials/`.
- Messenger Z demo mode:

```bash
adb shell am start -n dev.eziedutech.dcai.samplechat/.MainActivity --es demo open
```

Other values: `focus`, `card`, `landscape`, `next`, `image`, `restart`, `back`.

## Scenario

| # | Time | Screen | Shows |
|---|---|---|---|
| 1 | 0:00-0:15 | Homepage | Problem and promise |
| 2 | 0:15-0:35 | Phone: onboarding, persistent notification, Protection tab | Visible to the child; parent PIN |
| 3 | 0:35-1:15 | Phone: Messenger Z, chat with Kak Bima (demo `open`, `next`); dashboard live beside it | Gradual pattern, child reminder, level rises, parent insight |
| 4 | 1:15-1:35 | Phone: student card about to be shared (demo `card`) | Personal data blurred before sending |
| 5 | 1:35-1:50 | Phone: gambling site held | Category and reason; server gets category only |
| 6 | 1:50-2:10 | Phone: break screen or focus mode (demo `focus`); dashboard time request | Healthy habits; parent decides |
| 7 | 2:10-2:25 | Dashboard: Ask dcAI | Answer from dashboard data only |
| 8 | 2:25-2:40 | `/sekolah` | Anonymous counts per class |
| 9 | 2:40-3:00 | Flow diagram, results, limits | Meta at the core; close |

## Transcript (English narration)

1. Children meet strangers, bullies and risky invitations in their chats. Most parental tools either block everything or show parents everything. dcAI guides the child first, then helps the parent understand.
2. The parent installs dcAI on the child's phone, and they read the consent together. dcAI is always visible. Switching a protection off needs the parent's PIN, and the parent is told.
3. Here a stranger slowly builds closeness, asks for secrecy, then asks to move to another app. Names and numbers are masked on the phone before anything leaves. A distilled Llama 3.1 8B labels each message; Muse Spark assesses the conversation. The child gets a short reminder with the reason. The parent sees the level, the pattern and three ways to start the conversation. Never the message text.
4. When the child is about to share a student card, dcAI finds the name, school, address and phone on the phone and blurs them before it is sent. In chat apps with the dcAI SDK, sexual images are blurred too. Images never leave the phone.
5. Sites are matched on the phone against 5.1 million listed domains. A gambling site is held with the reason. The server learns only the category.
6. Daily limits, bedtime and focus mode build healthy habits. The child can ask for more time; Muse Spark suggests an answer, and the parent decides.
7. Parents can ask dcAI in their own words. Muse Spark answers only from what the dashboard already shows, with the child as an alias.
8. With the parent's separate consent, a school sees anonymous counts per class, only when at least five children take part. Never a single child.
9. Meta's models are at the core: Muse Spark for assessment, guidance and answers; Llama, distilled from Muse Spark, for every message, at 46 percent lower cost with the same safety results on our locked test split. An optional Llama 3.2 1B runs on the phone itself. A deterministic rule floor means a model failure is never shown as safe. All data here is synthetic, and dcAI is not yet tested with real families. Built with Llama. dcAI: guide first, then understand.

## Subtitle (Bahasa Indonesia)

1. Anak bertemu orang asing, perundungan, dan ajakan berisiko di chat. Kebanyakan alat orang tua memblokir semuanya atau menampilkan semuanya ke orang tua. dcAI membimbing anak dulu, lalu membantu orang tua memahami.
2. Orang tua memasang dcAI di HP anak, dan mereka membaca persetujuan bersama. dcAI selalu terlihat. Mematikan perlindungan butuh PIN orang tua, dan orang tua diberi tahu.
3. Di sini orang asing perlahan membangun kedekatan, meminta rahasia, lalu mengajak pindah aplikasi. Nama dan nomor disamarkan di HP sebelum apa pun keluar. Llama 3.1 8B hasil distilasi memberi label tiap pesan; Muse Spark menilai percakapan. Anak mendapat pengingat singkat beserta alasannya. Orang tua melihat level, pola, dan tiga cara memulai percakapan. Tanpa isi pesan.
4. Saat anak akan membagikan kartu pelajar, dcAI menemukan nama, sekolah, alamat, dan telepon di HP dan mengaburkannya sebelum terkirim. Di aplikasi chat dengan SDK dcAI, gambar seksual juga dikaburkan. Gambar tidak pernah keluar dari HP.
5. Situs dicocokkan di HP dengan 5,1 juta domain terdaftar. Situs judi ditahan beserta alasannya. Server hanya tahu kategorinya.
6. Batas harian, jam tidur, dan mode fokus membangun kebiasaan sehat. Anak bisa minta tambahan waktu; Muse Spark menyarankan jawaban, orang tua yang memutuskan.
7. Orang tua bisa bertanya ke dcAI dengan kata-kata sendiri. Muse Spark menjawab hanya dari yang sudah tampil di dasbor, dengan nama anak diganti alias.
8. Dengan persetujuan terpisah dari orang tua, sekolah melihat jumlah anonim per kelas, hanya bila minimal lima anak ikut. Tidak pernah satu anak.
9. Model Meta menjadi inti: Muse Spark untuk penilaian, bimbingan, dan jawaban; Llama hasil distilasi dari Muse Spark untuk setiap pesan, dengan biaya 46 persen lebih rendah dan hasil keselamatan yang sama pada test split terkunci kami. Llama 3.2 1B pilihan berjalan langsung di HP. Lantai aturan deterministik memastikan kegagalan model tidak pernah tampil sebagai aman. Semua data di sini sintetis, dan dcAI belum diuji dengan keluarga nyata. Dibuat dengan Llama. dcAI: bimbing dulu, lalu pahami.

Numbers in the narration: 5.1 million, 46 percent, five. Sources: README Results and `eval/distill/report.md`. Add no other figure.
