# Deploy dcAI di Dokploy: 3 service dalam 1 project

Produksi memakai tiga service terpisah di dalam satu Project Dokploy, bukan satu resource
Compose. Database dikelola Dokploy sendiri, jadi siklus hidupnya lepas dari deploy aplikasi
dan rebuild app tidak pernah menyentuh datanya. Ini menggantikan resource Compose lama
(`dcai-gugzsn`).

Semua konfigurasi aplikasi lewat variabel lingkungan (`DATABASE_URL`, `DCAI_API_URL`), jadi
tidak ada kode yang perlu diubah untuk pemisahan ini.

## Topologi

Satu Project (misalnya `dcai / production`) berisi:

- **dcai-db**: Database PostgreSQL yang dikelola Dokploy. Volume dan siklus hidupnya terpisah.
- **dcai-api**: Application (backend FastAPI), build dari Dockerfile. Domain path `/v1` ke port 8000.
- **dcai-web**: Application (Next.js), build dari Dockerfile. Domain path `/` ke port 3000.

## 1. Database (dcai-db)

- Create Service > Database > PostgreSQL 18. Nama database `dcai`, user `dcai`, password kuat.
- Catat host internal yang ditampilkan Dokploy (alias service DB) dan port 5432.
- Connection string untuk api:
  `postgresql+psycopg://dcai:<password>@<host-internal-db>:5432/dcai`

## 2. Backend (dcai-api)

- Create Service > Application, sumber repo GitHub ini, branch `main`.
- Build Type: Dockerfile.
  - Dockerfile Path: `code/backpy/Dockerfile`
  - Build Context: `.` (root repo) -> penting, Dockerfile meng-COPY `code/backpy` dan `data/guide` dari root.
- Port: 8000. Domain: path `/v1`, port 8000, tanpa strip path (API ponsel bergantung pada awalan `/v1`).
- Environment: `DATABASE_URL` (dari langkah 1), `SECRET_KEY`, dan semua variabel model
  (`REASONING_ENDPOINTS`, `SCREENING_ENDPOINTS`, `META_*`, `FIREWORKS_*`, `FW_MUSE_*`,
  `WB_STUDENT_*`, `WB_LLAMA70B_*`, `BT_MUSE_*`, `LLM_TIMEOUT_SECONDS`). Salin nilainya dari
  resource Compose lama. Nilai rahasia tidak pernah masuk repo.
- Migrasi otomatis: container menjalankan `alembic upgrade head` saat start (`deploy/start.sh`),
  jadi skema dibuat sendiri pada deploy pertama.

## 3. Web (dcai-web)

- Create Service > Application, sumber repo ini, branch `main`.
- Build Type: Dockerfile.
  - Dockerfile Path: `code/frontnext/Dockerfile`
  - Build Context: `code/frontnext`
- Port: 3000. Domain: path `/`, port 3000.
- Environment: `DCAI_API_URL` = URL internal service api, misalnya `http://dcai-api:8000`
  (pakai alias internal api di Dokploy). Web memanggil backend hanya dari sisi server.

## 4. Jaringan internal

Service dalam satu Project berbagi jaringan Dokploy: api mengakses DB lewat host internalnya,
web mengakses api lewat `DCAI_API_URL`. Tidak ada port yang dipublikasi langsung; akses publik
hanya lewat domain (Traefik) untuk web (`/`) dan api (`/v1`).

## 5. Cutover dari Compose lama

Data saat ini sintetis, jadi reset bersih paling sederhana:

1. Buat ketiga service di atas dalam satu Project.
2. Deploy `dcai-db`, lalu `dcai-api` (migrasi jalan pada skema kosong), lalu `dcai-web`.
3. Uji: `GET https://<domain>/v1/health`, buka dashboard orang tua dan `/sekolah`.
4. Setelah yakin, hentikan atau arsipkan resource Compose lama (`dcai-gugzsn`) agar tidak dobel.

Bila ingin mempertahankan data: `pg_dump` dari DB Compose lama lalu restore ke DB terkelola
baru sebelum mendeploy api (perlu akses sementara ke kedua database).

## 6. Autodeploy

Daftarkan webhook deploy Dokploy untuk `dcai-api` dan `dcai-web` ke push `main` di GitHub
(seperti yang sudah dilakukan untuk resource Compose). Database tidak perlu webhook.

## 7. Model on-device (Llama di ponsel)

Mode analisis "di ponsel" mengunduh model stage 1 (Llama 3.2 3B distilasi) dari backend.
Backend menyajikannya dari direktori `ONDEVICE_MODEL_DIR`, digerbang device token:

- `GET /v1/device/model/stage1/manifest` (version, ukuran, sha256)
- `GET /v1/device/model/stage1.pte`
- `GET /v1/device/model/stage1-tokenizer.json`

Bila `ONDEVICE_MODEL_DIR` kosong atau berkas tak ada, ketiganya menjawab 404 (default aman:
mode di ponsel tidak ditawarkan). Berkas TIDAK pernah masuk repo (sekitar 2 GB, gitignored).

Langkah di produksi (dcai-api):

1. Pasang mount persisten ke `dcai-api`: bind mount dari direktori host (mis. `/srv/dcai-model`)
   ke `/srv/model` di container, READ-ONLY. Bind mount dipilih agar berkas 2 GB mudah ditaruh
   dan tetap ada melintasi rebuild/redeploy.
2. Unggah dua berkas ke lokasi itu (dari laptop, berkas ada di laptop dan gitignored). Nama di
   direktori WAJIB `stage1.pte` dan `tokenizer.json`:

   ```bash
   scp out/Llama-3.2-3B-dcai-stage1/model.pte USER@HOST:/srv/dcai-model/stage1.pte
   scp out/Llama-3.2-3B-dcai-stage1/tokenizer/tokenizer.json USER@HOST:/srv/dcai-model/tokenizer.json
   chmod 644 /srv/dcai-model/stage1.pte /srv/dcai-model/tokenizer.json   # terbaca uid 10001
   ```

   Host perlu ruang kosong sekitar 2,1 GB.
3. Set env `ONDEVICE_MODEL_DIR=/srv/model` di `dcai-api` (pertahankan semua env lain).
4. Redeploy `dcai-api`.
5. Verifikasi: `GET https://dcai.digitalsafe.app/v1/device/model/stage1/manifest` dengan device
   token terpasang -> 200; `pte_bytes` cocok dengan ukuran berkas laptop dan `pte_sha256` cocok
   dengan `sha256sum model.pte`.

Urutan penting: unggah berkas dan pasang mount SEBELUM set env dan redeploy, supaya permintaan
pertama sudah menemukan berkasnya.

## Catatan

`code/docker-compose.prod.yml` tetap ada untuk pengembangan lokal dan rujukan; produksi
memakai tiga resource di atas.
