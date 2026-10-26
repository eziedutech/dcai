# AGENTS.md

Salinan bagian 14 dari spesifikasi pembangunan dcAI, tanpa perubahan isi.

Penyesuaian struktur repo (alasan: aturan susunan folder pemilik proyek):

| Usulan di bawah | Tempat di repo ini |
| --- | --- |
| `backend/` | `code/backpy/` |
| `web/` | `code/frontnext/` |
| `android-ime/` | `code/android-ime/` |
| `data/`, `eval/` | `data/`, `eval/` di akar repo |

## 14. Panduan untuk agent coding

Bagian ini bisa disalin ke `AGENTS.md` di repo dan menjadi instruksi tetap bagi agent coding; bagian lain dokumen ini adalah rujukannya.

**Misi:** bangun Digital Safe dcAI sesuai bagian 4 sampai 9 dalam 10 hari, dengan satu alur demo yang tahan live. Prioritas: alur demo berjalan, klaim privasi benar, lalu kerapian.

**Urutan membaca:** bagian 4 (lingkup), 8 (modul), 10 (privasi), 12 (rencana), lalu sisanya.

**Struktur repo yang diusulkan:**

```text
dcai/
  AGENTS.md              salinan bagian 14
  README.md              cara menjalankan, keterbatasan, jejak kerja
  Makefile               perintah standar
  .env.example           nama variabel, tanpa nilai
  docs/                  keputusan arsitektur (ADR), log harian
  backend/               FastAPI, modul risk, coach, consent, privacy, sim
    app/
      llm/               LLMClient, MuseClient, OpenWeightsClient
      risk/              tahap 1, tahap 2, lantai aturan, skema
      coach/             prompt dan skema keluaran
      privacy/           penyamaran, deteksi data pribadi
      api/               rute /v1
    tests/
  web/                   Next.js: homepage dan dasbor
  android-ime/           Kotlin IME minimal
  data/
    scenarios/           skenario sintetis (JSON)
    replay/              keluaran model tersimpan untuk mode replay
  eval/                  skrip dan laporan evaluasi
```

**Variabel lingkungan** (nama saja; nilai tidak pernah masuk repo):

```text
META_API_KEY=
META_API_BASE=https://api.meta.ai/v1
MUSE_MODEL=              ID model Muse Spark terbaru dari GET /v1/models
OPENWEIGHTS_BASE=        penyedia inferensi untuk Llama
OPENWEIGHTS_API_KEY=
OPENWEIGHTS_MODEL=
DATABASE_URL=
SECRET_KEY=
EVIDENCE_ENC_KEY=
REPLAY_MODE=false
```

**Perintah standar (`Makefile`):** `make setup`, `make dev`, `make test`, `make eval`, `make seed` (muat skenario), `make replay-record` (rekam keluaran model), `make lint`.

**Aturan kerja agent:**

1. Kerjakan satu hari dari bagian 12 dalam satu waktu, dan hentikan bila definisi selesai hari itu belum terpenuhi sebelum maju.
2. Jangan menambah fitur di luar tabel bagian 4. Bila terasa perlu, tulis usulan di `docs/` dan tunggu keputusan manusia.
3. Semua keluaran model berupa JSON yang divalidasi skema. Tidak ada teks bebas yang dipercaya langsung.
4. Tidak ada kolom, log, atau fixture berisi teks percakapan mentah di luar `data/scenarios` (data sintetis). Tambahkan pengujian yang gagal bila teks pesan muncul di log atau respons dasbor.
5. Jangan pernah memakai atau menyalin data nyata anak, data siswa, atau data klien dari proyek lain.
6. Jangan menulis nomor versi model di kode; ambil dari `MUSE_MODEL`.
7. Jangan mengarang nomor telepon, situs layanan, kutipan hukum, statistik, atau klaim akurasi. Angka hanya dari `eval/report.md`.
8. Terminologi UI mengikuti tabel di bagian 3. Jangan memakai kata "memonitor" atau "memata-matai" di teks yang tampil ke pengguna.
9. Rahasia hanya di variabel lingkungan. Jalankan pemindaian rahasia sebelum setiap push.
10. Commit kecil dengan pesan jelas. Tulis log harian singkat di `docs/log/` (selesai, meleset, keputusan).
11. Bila ada ketidakjelasan yang memengaruhi lingkup, privasi, atau klaim, berhenti dan tanya manusia; jangan menebak.

**Kerangka prompt Tahap 2 (Muse Spark), tingkat pola saja:**

```text
Peran: analis keselamatan anak yang berhati-hati. Kamu menerima label perilaku
per pesan dan paling banyak 6 kutipan tersamarkan dari 10 pesan terakhir.
Tugas: nilai apakah pola menunjukkan pendekatan berisiko terhadap anak.
Aturan: jangan menuduh; beri keyakinan; bedakan obrolan wajar dari pola
bertahap; jangan mengulang kutipan di rationale_for_parent.
Keluaran: HANYA JSON sesuai skema (risk_score, level, patterns_observed,
trajectory, rationale_for_parent, confidence).
```

**Kerangka prompt Citizenship Coach:**

```text
Peran: pendamping kewarganegaraan digital yang hangat. Masukan: level,
pola, rentang usia anak, bahasa. Keluaran JSON: child_nudge (maks 2 kalimat),
parent_insight (apa yang terlihat, mengapa penting, 3 pembuka percakapan,
hal yang sebaiknya dan tidak sebaiknya dilakukan), micro_lesson (opsional).
Aturan: tidak menyalahkan anak, tidak menyuruh menghukum, tidak mengarang
nomor atau situs layanan, pakai daftar kanal dari konfigurasi.
```

**Tugas awal untuk agent (hari 1):**

- [ ] Buat monorepo sesuai struktur di atas dan `Makefile` yang berjalan.
- [ ] Implementasikan `LLMClient` dan `MuseClient` dengan satu panggilan nyata ke API, memakai `MUSE_MODEL`.
- [ ] Implementasikan `OpenWeightsClient` sebagai cadangan dengan antarmuka yang sama.
- [ ] Tambahkan skema Pydantic untuk keluaran Tahap 2 dan Coach, beserta pengujian validasi.
- [ ] Tambahkan pengujian yang gagal bila teks pesan muncul di log.
- [ ] Atur CI: lint dan uji pada setiap push.
- [ ] Tulis `README.md` awal, termasuk bagian keterbatasan dan peringatan data sintetis.

**Definisi selesai (berlaku untuk setiap modul):** pengujian unit lulus; keluaran lolos validasi skema; perilaku gagal diuji; tidak ada teks mentah di log; terminologi sesuai; tercatat di log harian; dan modul tampil di alur demo bagian 5.
