# Usulan 0002: Arah C, dcAI Guardian di perangkat anak

Status: diterima pemilik, 27 Oktober 2026. Menggantikan lingkup MVP di spesifikasi bagian 4.

Sumber diverifikasi 27 Oktober 2026 dan dicantumkan per baris. Yang belum bisa dicek dari sumber resmi ditandai "belum terverifikasi".

## 1. Ringkasan

dcAI menjadi lapisan kedua di samping Google Family Link. Family Link mengatur batas: aplikasi, waktu layar, pembelian, dan lokasi. dcAI memahami isi di seluruh perangkat anak, membimbing anak saat itu juga, dan memberi orang tua insight. Orang tua yang memasang dan mengendalikan. Android dulu.

## 2. Keputusan yang sudah diambil pemilik

| Topik | Keputusan |
| --- | --- |
| Arah produk | C: perlindungan aktivitas anak di perangkatnya, dipasang dan dikendalikan orang tua |
| Model di perangkat | Bertingkat: aturan penyamaran dan classifier kecil di ponsel; hanya yang ditandai, setelah disamarkan, ke cloud; tidak ada LLM di ponsel |
| Pemicu visual | Ketiganya: gambar di percakapan berisiko, gambar yang akan dibagikan anak, situs yang ditandai |
| Gambar sensitif | Dikaburkan sekabur-kaburnya, tidak pernah keluar dari ponsel |
| Salah deteksi gambar | Anak menunjukkan ke orang tua, orang tua mengonfirmasi. Tingkat 1: perceptual hash dan ambang di ponsel itu. Tingkat 2: hanya sinyal (kategori, skor, versi model) ke server. Federated learning masuk roadmap |
| Fine-tuning | Distilasi ke model Meta yang lebih kecil. Di W&B hanya Llama 3.1 8B yang tersedia (lihat 4.2); Glimmer dicari di layanan lain |
| Self-host | Ya, bertahap, sebagai rencana di pitch |
| Asisten orang tua | Masuk MVP: Muse Spark dengan tool calling, hanya mengakses insight |
| Lingkup | Arah ini menggantikan lingkup MVP spesifikasi bagian 4 |
| Usia fokus | Kelas tinggi SD sampai SMA, 10 sampai 17 tahun; rentang usia 10-12, 13-15, 16-17 |
| Model bisnis | Bertahap: freemium keluarga dan pilot sekolah lebih dulu, operator dan produsen ponsel setelah ada bukti dampak |
| Pemotongan lingkup | Tidak ada; semua bagian dituntaskan |

## 3. Posisi terhadap Family Link

Halaman bantuan Family Link (support.google.com/families/answer/7101025) menyebut: mengelola akun, menyetujui dan memblokir aplikasi, mengatur izin, waktu layar dan jadwal tidur, membatasi konten dewasa di Google Play, persetujuan pembelian Play, dan lokasi perangkat. Halaman itu tidak menyebut analisis isi pesan, gambar di layar, atau peringatan kepada anak tentang percakapan berisiko. Family Link juga tidak bisa mengawasi iPhone.

Kalimat posisi yang diusulkan: "Family Link untuk batas, dcAI untuk pemahaman." dcAI tidak bersaing dengan alat gratis Google; orang tua pengguna Family Link adalah pasar pertama.

## 4. Fakta teknis dan kebijakan

### 4.1 Android

| Fakta | Sumber |
| --- | --- |
| `AccessibilityService.takeScreenshot` (API 30, Android 11) mengambil tangkapan layar tanpa dialog per panggilan; layanan wajib mendeklarasikan `canTakeScreenshot`. Dokumentasi menyebut API ini "can be used for machine learning-based visual screen understanding". Ada galat bila jeda antar tangkapan terlalu pendek | developer.android.com, AccessibilityService |
| Google Play mengizinkan aplikasi pemantauan hanya bila dibuat dan dipasarkan khusus untuk orang tua mengawasi anak (atau pemberi kerja), dengan flag manifest `IsMonitoringTool` | Kebijakan Malware, bagian stalkerware (answer/9888380) |
| Syaratnya: tidak tampil sebagai alat mata-mata, tidak menyembunyikan pemantauan, notifikasi tetap selama berjalan, ikon unik, pengungkapan di deskripsi Play | sama |
| AccessibilityService untuk aplikasi pemantauan: boleh, tetapi tidak boleh mengaku sebagai alat aksesibilitas, wajib pengungkapan di dalam aplikasi dengan persetujuan aktif dan video demo saat pengajuan | Kebijakan AccessibilityService (answer/10964491) |
| API aksesibilitas tidak boleh dipakai mencegah pencopotan aplikasi, kecuali diizinkan orang tua lewat aplikasi kontrol orang tua | Permissions and APIs (answer/9888170) |
| VpnService: aplikasi kontrol orang tua dikecualikan dari aturan VPN-only, tetapi tetap wajib pengungkapan dan persetujuan | sama |

Akibat untuk rancangan: semua prinsip transparansi kita (anak tahu, indikator selalu tampil, tidak ada mode tersembunyi) ternyata juga syarat Google Play. Prinsip produk dan syarat distribusi sejalan.

### 4.2 Meta

| Fakta | Sumber |
| --- | --- |
| Muse Spark 1.1, 1.2, 1.3: masukan teks, gambar, video, audio, PDF; konteks 1.048.576 token; 1.3 direkomendasikan | dev.meta.ai/docs/models |
| Mode Standard: "your content is not used to train Meta models". Varian `-contributor` memakai konten untuk melatih model Meta dengan harga lebih murah. Kita memakai `muse-spark-1.3` (Standard) | dev.meta.ai/docs/pricing-rate-limits |
| Harga Muse Spark (Standard): input 1,25, cached 0,15, output 4,25 USD per juta token, sama dengan Fireworks | sama |
| SAM 3.1: frasa benda (misalnya "face") pada gambar atau video, keluar kotak dan masker per piksel; satu konsep per permintaan; 2,50 USD per 1.000 gambar | dev.meta.ai/docs/sam/overview, pricing |
| Muse Voice Transcribe: 0,18 USD per jam audio, 25 bahasa, realtime | pricing, models |
| Muse Image: 0,01 USD per gambar, untuk data uji visual sintetis | pricing |
| Muse Wonder: model paling mampu untuk rekayasa perangkat lunak dan agen jangka panjang, 4 dan 20 USD per juta token. Tidak dibutuhkan untuk dcAI | models, pricing |
| Muse Glimmer: 30B, "distilled from Muse Spark", teks dan gambar, lebih dari 100 bahasa, lisensi Apache 2.0, bisa di-host sendiri (vLLM, SGLang, llama.cpp, Ollama) | dev.meta.ai/docs/muse-glimmer |
| Muse Spark Open: 816B total, 42B aktif; NVFP4 sekitar 537 GB, satu node 4 GPU Blackwell; lisensi "Muse Model License" plus Acceptable Use Policy; pemakaian komersial belum dikonfirmasi dari teks lisensi | dev.meta.ai/docs/muse-spark-open |
| ExecuTorch: runtime on-device dari PyTorch untuk Android dan iOS, dengan API Java | docs.pytorch.org/executorch |

Belum terverifikasi: apakah kredit gratis Meta mengubah aturan mode Standard (layar billing menyebut konten "may be used for product improvement" saat memakai kredit gratis, dokumentasi tidak menyebut kredit gratis).

### 4.3 W&B Serverless Training (CoreWeave)

| Fakta | Sumber |
| --- | --- |
| Model yang bisa dilatih (SFT dan RL): `meta-llama/Llama-3.1-8B-Instruct`, `google/gemma-4-26B-A4B-it`, `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B`, `Qwen/Qwen3.8-27B`, `Qwen/Qwen3.6-35B-A3B`. Muse Glimmer tidak ada | docs.coreweave.com, available-models |
| Training gratis selama public preview; yang dibayar inference (harga Serverless Inference) dan penyimpanan (gratis minimal 5 GB, sekitar 30 LoRA) | usage-limits |
| Setiap checkpoint otomatis bisa dipanggil tanpa deployment sendiri | docs.coreweave.com/training |

### 4.4 iOS

Belum terverifikasi dari halaman resmi (halaman Apple tidak terbaca). Menurut pengetahuan umum, Screen Time API (FamilyControls, ManagedSettings, DeviceActivity) hanya membolehkan memilih, membatasi, dan menjadwalkan aplikasi dengan token buram, tanpa akses ke isi layar atau pesan aplikasi lain. Akibatnya arah C pada dasarnya Android.

## 5. Arsitektur yang diusulkan

```
Ponsel anak (Android)                                   Cloud dcAI
  AccessibilityService: teks layar, peristiwa         
  IME (opsional): teks yang diketik                   
  VpnService lokal: domain yang ditandai              
        |                                              
  Penyamaran (aturan, port dari Python, kasus uji sama)
  Classifier teks kecil (ExecuTorch, distilasi)  --ditandai, tersamarkan-->  Tahap 1 (Llama/model hasil distilasi)
  Pemicu visual -> takeScreenshot                                              lantai aturan
     OCR, deteksi wajah, classifier gambar sensitif                            Tahap 2 Muse Spark
     sensitif: kabur penuh di layar, tidak dikirim                             Coach Muse Spark
     tidak sensitif dan ambigu: diperkecil, wajah dan teks pribadi             Muse Spark vision, SAM 3.1
        dikaburkan, lalu dikirim  -------------------------------------------> label saja yang disimpan
  Overlay nudge untuk anak  <---------------------------------------------- nudge, level
                                                                              Dasbor orang tua, SSE
                                                                              Tanya dcAI (tool calling)
```

Yang dipakai ulang dari kode sekarang: pool model, penyamaran (sebagai spesifikasi untuk port Kotlin), tahap 1 dan 2, lantai aturan, Coach, persetujuan, evaluasi. Perkiraan sekitar 70 persen.

## 6. Peran Meta

| Peran | Komponen Meta |
| --- | --- |
| Guru dan penalaran inti | Muse Spark 1.3 |
| Penyaring cloud dan murid | Llama 3.3 70B, lalu Llama 3.1 8B hasil SFT di W&B; Glimmer 30B sebagai pembanding bila ada layanan |
| Mata | Muse Spark vision, SAM 3.1 |
| Telinga | Muse Voice Transcribe |
| Data uji visual sintetis | Muse Image |
| Di perangkat | ExecuTorch |
| Asisten orang tua | Muse Spark dengan tool calling |
| Produksi di wilayah pengguna | Glimmer (Apache 2.0) dan Llama di-host sendiri; Muse Spark Open bila lisensi mengizinkan |

## 7. Risiko yang tersisa

1. Distribusi Play Store: syarat `IsMonitoringTool`, pengungkapan, dan video demo harus lulus tinjauan Google. Untuk hackathon dan pilot cukup APK langsung.
2. Hukum: materi seksual anak tidak pernah dikirim atau disimpan; jalur salah deteksi tingkat 1 dan 2 tidak memindahkan gambar. Perlu tinjauan penasihat hukum sebelum pemakaian nyata.
3. Classifier gambar sensitif tidak diuji dengan gambar sungguhan; ditulis sebagai rancangan.
4. Baterai dan kinerja di ponsel kelas bawah belum diukur.
5. Remaja dapat mencoba mematikan; Device Owner atau supervisi membantu.
6. Kredit gratis Meta dan data (4.2, belum terverifikasi).

## 8. Rencana pembangunan

Urutan mengikuti ketergantungan. Setiap tahap selesai bila tesnya lulus, klaimnya terukur, dan tercatat di log harian.

| Tahap | Isi |
| --- | --- |
| 1. Backend untuk perangkat | Rentang usia baru; ruang lingkup persetujuan baru (teks layar, gambar, domain); pasangan perangkat dan token perangkat; API masuk dari perangkat (pesan tersamarkan, label gambar, sinyal salah deteksi); tahap 2 dan Coach di latar belakang; SSE; harga Meta di konfigurasi |
| 2. Dasbor orang tua (Next.js) | Ringkasan, insight, peristiwa, pengaturan, hapus data, "Cara AI membantu", Tanya dcAI dengan tool calling, homepage dan halaman privasi |
| 3. Aplikasi Android dcAI Guardian (Kotlin) | Penyiapan oleh orang tua dan persetujuan, layar transparansi anak, notifikasi tetap, AccessibilityService untuk teks, port penyamaran dengan kasus uji yang sama, overlay nudge, flag IsMonitoringTool |
| 4. Aplikasi chat contoh dan simulator | Aplikasi chat sintetis buatan sendiri di Android untuk demo, pemutar skenario dengan mode replay |
| 5. Visual | Pemicu, takeScreenshot, OCR dan deteksi wajah di perangkat, classifier gambar sensitif di perangkat, kabur penuh, jalur cloud Muse Spark vision dan SAM 3.1, data uji sintetis dari Muse Image, salah deteksi tingkat 1 dan 2 |
| 6. Distilasi | Data latih sintetis lebih besar, label dari guru, SFT Llama 3.1 8B di W&B, evaluasi terhadap 70B, classifier teks kecil di perangkat lewat ExecuTorch |
| 7. Domain | VpnService lokal dengan daftar domain yang sumber dan lisensinya jelas |
| 8. Suara | Voice note lewat Muse Voice Transcribe |
| 9. Evaluasi akhir dan pengiriman | Set uji terkunci, unit economics terukur, README, video, deskripsi, pengiriman |

Yang perlu dicek sebelum tahap 3 dan 5: perangkat dan SDK Android di mesin ini, model classifier gambar sensitif dengan lisensi yang jelas, dan sumber daftar domain.
