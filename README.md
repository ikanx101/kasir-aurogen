# Kasir Dapoerasatoe

Aplikasi kasir berbasis web untuk event bazaar. Dioptimalkan untuk layar tablet 7–10 inci.

---

## Fitur

- **Manajemen Event** — buat, edit, aktifkan/nonaktifkan event bazaar
- **Manajemen Menu** — CRUD menu item (nama, harga, stok) per event; stok tidak bisa minus
- **POS / Kasir** — grid menu + keranjang belanja, finger-friendly, notifikasi stok tidak cukup
- **Data Pelanggan & Pembayaran** — saat checkout kasir mengisi nama pelanggan, nomor HP/WA (opsional), dan metode pembayaran (Tunai / QRIS)
- **Struk PNG** — generate dan download struk otomatis setelah transaksi; menyertakan **logo usaha**, info pelanggan, dan metode pembayaran
- **Rekap Admin** — tabel omset per event, breakdown Tunai vs QRIS, riwayat transaksi + detail per nomor (termasuk info pelanggan)
- **Edit & Hapus Struk** — admin dapat mengedit qty item atau menghapus struk; **stok otomatis dikembalikan** ke kondisi sebelum transaksi
- **Logo di semua halaman** — logo usaha (`logo_utama.jpeg`) tampil di header setiap halaman

---

## Cara Menjalankan Lokal

### Prasyarat
- Python 3.10 atau lebih baru
- pip

### Langkah

```bash
# 1. Masuk ke folder project
cd kasir_app

# 2. Install dependensi
pip install -r requirements.txt

# 3. Jalankan server
uvicorn app.main:app --reload --port 8000
```

Buka di browser: **http://localhost:8000**

Login admin: password **`admin123`** (ganti sebelum production via env var `ADMIN_PASSWORD`)

Database SQLite dibuat otomatis di `kasir.db` saat pertama jalan.

---

## Struktur Project

```
kasir_app/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Baca env vars
│   ├── database.py          # SQLAlchemy session
│   ├── models.py            # Tabel: Event, MenuItem, Transaction, TransactionItem
│   ├── templates_config.py  # Shared Jinja2 templates instance (path absolut)
│   ├── routers/
│   │   ├── auth.py          # Login / logout admin
│   │   ├── events.py        # CRUD event (+ bersihkan file PNG saat hapus)
│   │   ├── menu.py          # CRUD menu item
│   │   ├── pos.py           # POS, transaksi (no. unik UUID), download struk
│   │   └── admin.py         # Rekap omset, riwayat, edit & hapus transaksi
│   ├── templates/           # HTML (Jinja2 + Tailwind CSS + Alpine.js)
│   ├── static/
│   │   ├── logo_utama.jpeg  # Logo usaha (tampil di header & struk PNG)
│   │   └── struk/           # Output PNG struk (di-mount ke Railway Volume)
│   └── utils/
│       └── struk_gen.py     # Generator PNG via Pillow (termasuk logo)
├── requirements.txt
├── Procfile                 # Perintah start untuk Railway
├── railway.json             # Konfigurasi Railway
├── nixpacks.toml            # Install font sistem di Railway
└── .env.example             # Template environment variables
```

---

## Environment Variables

Salin `.env.example` → `.env` untuk development lokal.

| Variable | Default | Keterangan |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./kasir.db` | URL koneksi database |
| `STRUK_DIR` | `./app/static/struk` | Folder simpan PNG struk |
| `SECRET_KEY` | *(default dev)* | Key sesi cookie — **wajib ganti di production** |
| `ADMIN_PASSWORD` | `admin123` | Password login admin — **wajib ganti di production** |
| `CASHIER_PASSCODE` | *(kosong)* | Passcode kasir opsional |

---

## Alur Penggunaan

```
[Pra-Event]
    Admin buat event → input menu & stok
        ↓
[Saat Event]
    Kasir buka POS → tap item → "Buat Struk"
        → isi nama pelanggan, HP/WA (opsional) + pilih metode pembayaran (Tunai/QRIS)
        → konfirmasi → PNG terdownload
        ↓  (stok berkurang otomatis)
[Koreksi]
    Admin buka Rekap → klik "Lihat" pada transaksi
        → Edit qty item (stok terkoreksi otomatis)
        → atau Hapus struk (stok dikembalikan penuh)
        ↓
[Pasca-Event]
    Admin lihat rekap omset & top item terlaris
```

---

## Deploy ke Railway.app

### Persiapan Awal

Sebelum mulai, pastikan sudah punya:
1. **Akun Railway** — daftar gratis di [railway.app](https://railway.app) (login via GitHub)
2. **Akun GitHub** — repository project ini sudah di-push ke GitHub
3. **Repository sudah ada** file: `Procfile`, `requirements.txt`, `nixpacks.toml`

---

### Langkah 1 — Push Project ke GitHub

Jika belum punya repo GitHub untuk project ini:

```bash
# Di folder kasir_app
git init
git add .
git commit -m "Initial commit: Kasir Dapoerasatoe"

# Buat repo baru di github.com, lalu:
git remote add origin https://github.com/USERNAME/kasir-dapoerasatoe.git
git push -u origin main
```

---

### Langkah 2 — Buat Project Baru di Railway

1. Buka **[railway.app](https://railway.app)** dan login
2. Klik tombol **"New Project"** (pojok kanan atas)
3. Pilih **"Deploy from GitHub repo"**
4. Pilih repository `kasir-dapoerasatoe` dari daftar
5. Klik **"Deploy Now"**

Railway akan langsung mulai proses build. Tunggu sampai statusnya **"Active"** (biasanya 2–3 menit).

> Jika ada error build, cek tab **"Deployments" → "View Logs"** untuk lihat detailnya.

---

### Langkah 3 — Tambah PostgreSQL

Aplikasi butuh database PostgreSQL untuk production (bukan SQLite).

1. Di halaman project Railway, klik **"+ New"**
2. Pilih **"Database"**
3. Pilih **"Add PostgreSQL"**
4. Railway otomatis membuat database dan **menyuntikkan `DATABASE_URL`** ke environment aplikasi Anda

Tidak perlu konfigurasi manual — Railway menghubungkan otomatis.

---

### Langkah 4 — Tambah Volume (Penyimpanan Struk PNG)

Volume diperlukan agar file PNG struk **tidak hilang saat deploy ulang**.

1. Klik service **aplikasi Anda** (bukan PostgreSQL) di dashboard project
2. Buka tab **"Settings"**
3. Gulir ke bagian **"Volumes"**
4. Klik **"Add a Volume"**
5. Isi:
   - **Mount Path**: `/app/app/static/struk`
   - **Size**: `1 GB` (sudah lebih dari cukup untuk ribuan struk)
6. Klik **"Create Volume"**

Railway akan restart aplikasi secara otomatis.

---

### Langkah 5 — Set Environment Variables

1. Klik service **aplikasi Anda**
2. Buka tab **"Variables"**
3. Klik **"New Variable"** dan tambahkan satu per satu:

| Variable | Nilai yang diisi |
|---|---|
| `SECRET_KEY` | String acak panjang, contoh: `x7k2p9m4n8q3r1j6w5y0` (minimal 32 karakter) |
| `ADMIN_PASSWORD` | Password pilihan Anda untuk login admin |
| `STRUK_DIR` | `/app/app/static/struk` |

> **Catatan:** `DATABASE_URL` **tidak perlu diisi manual** — sudah otomatis dari PostgreSQL di Langkah 3.

Setelah menambah variable, Railway otomatis deploy ulang.

---

### Langkah 6 — Akses Aplikasi

Setelah deploy selesai:

1. Buka tab **"Settings"** pada service aplikasi
2. Di bagian **"Domains"**, Railway sudah menyediakan domain otomatis:
   ```
   https://kasir-dapoerasatoe-production.up.railway.app
   ```
3. Klik domain tersebut — aplikasi Anda sudah online!

> Tabel database dibuat **otomatis saat pertama akses** — tidak perlu migrasi manual.

---

### Langkah 7 (Opsional) — Custom Domain

Jika ingin domain sendiri seperti `kasir.dapoerasatoe.com`:

1. Tab **"Settings"** → bagian **"Domains"** → klik **"Custom Domain"**
2. Ketik domain Anda, contoh: `kasir.dapoerasatoe.com`
3. Railway menampilkan **CNAME record** yang harus ditambahkan di DNS provider Anda
4. Masuk ke pengaturan DNS domain Anda, tambahkan:
   - **Type**: `CNAME`
   - **Name**: `kasir` (atau `@` untuk root domain)
   - **Value**: nilai yang diberikan Railway
5. Tunggu propagasi DNS (biasanya 5–30 menit)

---

### Ringkasan Langkah Deploy

```
1. Push ke GitHub
      ↓
2. Railway → New Project → Deploy from GitHub
      ↓
3. Railway → + New → Database → PostgreSQL
      ↓
4. Railway → Settings → Volumes → Mount /app/app/static/struk
      ↓
5. Railway → Variables → isi SECRET_KEY, ADMIN_PASSWORD, STRUK_DIR
      ↓
6. Akses via domain .railway.app
```

---

### Checklist Sebelum Go Live

- [ ] `SECRET_KEY` sudah diganti (bukan default)
- [ ] `ADMIN_PASSWORD` sudah diganti (bukan `admin123`)
- [ ] PostgreSQL sudah terhubung (`DATABASE_URL` terisi otomatis)
- [ ] Volume sudah di-mount di `/app/app/static/struk`
- [ ] File `logo_utama.jpeg` sudah ada di `app/static/`
- [ ] Coba login admin dan buat event test
- [ ] Coba transaksi dan download struk PNG (pastikan logo muncul di struk)
- [ ] Coba edit qty struk dari halaman Rekap — cek stok terkoreksi
- [ ] Coba hapus struk dari halaman Rekap — cek stok kembali
- [ ] Hapus event test sebelum mulai event sungguhan

---

### Troubleshooting

**App gagal start / error "Application failed to respond"**
→ Buka tab **Deployments → View Logs**. Paling sering penyebabnya adalah `SECRET_KEY` atau `ADMIN_PASSWORD` belum diisi, atau Volume belum terhubung.

**Struk PNG tidak tersimpan / hilang setelah deploy**
→ Pastikan Volume sudah di-mount di path yang tepat: `/app/app/static/struk`. Cek tab Settings → Volumes.

**Logo tidak muncul di struk**
→ Pastikan file `logo_utama.jpeg` ada di `app/static/logo_utama.jpeg`. File ini harus ikut di-commit ke GitHub.

**Error database saat pertama akses**
→ Pastikan PostgreSQL plugin sudah ditambahkan dan `DATABASE_URL` muncul di tab Variables. Tabel dibuat otomatis — tidak perlu langkah migrasi.

**Font struk terlihat kecil / jelek**
→ `nixpacks.toml` sudah menyertakan instalasi font DejaVu. Pastikan file ini ada di root repository saat push ke GitHub.

---

## Pengembangan Lokal vs Production

| Aspek | Lokal | Railway (Production) |
|---|---|---|
| Database | SQLite (`kasir.db`) | PostgreSQL (managed) |
| Struk path | `./app/static/struk/` | `/app/app/static/struk/` (Volume) |
| Jalankan | `uvicorn app.main:app --reload` | Otomatis via Procfile |
| Config | file `.env` | Railway → Variables |

---

## Expose ke HP Teman via ngrok (Development)

Untuk testing dari HP atau tablet, tanpa deploy ke internet:

```bash
# Jalankan server lokal
uvicorn app.main:app --port 8000

# Di terminal lain, expose ke internet
ngrok http 8000
```

ngrok akan memberi URL sementara seperti `https://abc123.ngrok.io` yang bisa dibuka dari HP mana pun.
