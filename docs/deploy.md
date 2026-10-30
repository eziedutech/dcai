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

## Catatan

`code/docker-compose.prod.yml` tetap ada untuk pengembangan lokal dan rujukan; produksi
memakai tiga resource di atas.
