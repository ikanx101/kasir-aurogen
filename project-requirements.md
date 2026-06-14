# Aplikasi Kasir Bazaar — Dapoerasatoe

> **Project Requirements Document**
> Versi: 2.0 — 14 Juni 2026 (diperbarui)

---

## 1. Ringkasan

Aplikasi kasir berbasis web yang dioptimalkan untuk layar tablet (7–10 inci). Digunakan oleh **Dapoerasatoe** untuk mencatat penjualan makanan dan minuman selama event bazaar. Output utama: **struk pembelian dalam format PNG** yang bisa langsung didownload dan ditunjukkan ke konsumen. Struk menyertakan **logo usaha** di bagian atas.

---

## 2. Identitas & Branding

| Item | Nilai |
|---|---|
| Nama usaha | **Dapoerasatoe** |
| Logo | `logo_utama.jpeg` — tampil di header semua halaman dan di dalam struk PNG |
| Tampil di | Header aplikasi (setiap halaman) |
| Multi-tenant | Tidak — 1 aplikasi = 1 usaha |

---

## 3. Fitur Utama

### 3.1 Event Management (Admin)

Admin bisa membuat dan mengelola **event bazaar**.

**Field event:**
| Field | Tipe | Contoh |
|---|---|---|
| Nama Event | Text | "Bazaar Kuliner GBK 2026" |
| Tanggal Mulai | Date | 2026-07-15 |
| Tanggal Akhir | Date | 2026-07-17 |

**Behavior:**
- Event bisa diaktifkan/dinonaktifkan
- Hanya event aktif yang bisa digunakan untuk bertransaksi
- Admin bisa melihat daftar semua event (lalu + sekarang)
- Saat event dihapus, **semua file PNG struk ikut dihapus dari disk** (tidak ada orphan files)

### 3.2 Menu Management (Pre-event)

Admin mengisi **daftar menu/jualan** sebelum event dimulai.

**Field menu item:**
| Field | Tipe | Keterangan |
|---|---|---|
| Nama SKU | Text | Contoh: "Ayam Geprek", "Es Teh Manis" |
| Harga | Number (Rupiah) | Contoh: 15000 |
| Stok | Number (Integer) | Jumlah tersedia untuk event ini |

**Behavior:**
- CRUD menu item (Create, Read, Update, Delete)
- Menu bersifat per-event — tiap event punya daftar SKU sendiri
- Harga dalam Rupiah (IDR), tanpa desimal

### 3.3 POS / Transaksi (Cashier Interface)

Tampilan utama kasir, diakses via tablet (mode landscape ideal).

**Layout:**
- **Panel kiri / utama:** Grid menu items (card-style). Tiap card menampilkan:
  - Nama SKU
  - Harga
  - Stok tersisa
  - Button "Tambah" (disabled jika stok = 0)
- **Panel kanan:** Keranjang belanja
  - Daftar item yang dipilih (nama, qty, subtotal)
  - Tombol + / − untuk ubah qty (touch-friendly, ukuran 36px)
  - Tombol hapus item
  - **Total keseluruhan**

**Flow:**
1. Tap item → masuk ke keranjang
2. Atur qty
3. Tap "Buat Struk" → struk PNG ter-generate dan otomatis ter-download
4. Stok item berkurang sesuai qty yang dibeli
5. Item dengan stok 0 akan tampil **disabled/greyed out** dan tidak bisa diklik
6. Jika stok tidak cukup → **error jelas ditampilkan**, transaksi tidak diproses (tidak ada silent clamp)

### 3.4 Struk PNG Generator

#### Format Tampilan

```
+============================+
|       [LOGO USAHA]         |
|      Dapoerasatoe          |
|  Bazaar Kuliner GBK 2026   |
| 15 Juli 2026 14:23 WIB     |
| No: TRX-20260615-A1B2C3    |
+----------------------------+
| Ayam Geprek  2 x 15.000    |
| Es Teh Manis 1 x  5.000    |
+----------------------------+
| TOTAL           Rp 35.000  |
+----------------------------+
| Terima kasih sudah berkun- |
| jung! Semoga berkah :)     |
+============================+
```

**Spesifikasi teknis struk PNG:**
| Parameter | Nilai |
|---|---|
| Format file | PNG |
| Resolusi | High-res (600px base width, scale 2x = 1200px) |
| Background | Putih bersih |
| Font | DejaVu Sans Mono (fallback: Liberation Mono) |
| Warna teks | Hitam (#1a1a1a) |
| Nama toko | Bold, ukuran lebih besar |
| Logo | Disisipkan centered setelah separator atas, max 180×80 px (base) |
| Nomor transaksi | Format: `TRX-YYYYMMDD-XXXXXX` (UUID-based, unik, tanpa race condition) |

**Isi struk:**
1. Separator atas (═══)
2. **Logo usaha** (centered)
3. Nama usaha (bold, besar)
4. Nama event
5. Tanggal & jam transaksi (WIB)
6. Nomor transaksi unik
7. Separator (───)
8. Daftar item (nama, qty × harga satuan)
9. Separator (───)
10. Total keseluruhan (bold)
11. Separator (───)
12. Footer ucapan terima kasih
13. Separator bawah (═══)

**Delivery:**
- Tidak dikirim ke WA
- Tidak connect ke printer
- Hanya **didownload** oleh kasir (trigger download via browser)
- Jika struk gagal dibuat (error Pillow/font): transaksi tetap tercatat di database, kasir diberi tahu

### 3.5 Admin Dashboard — Riwayat, Rekap & Koreksi Struk

Akses khusus admin untuk memantau dan mengelola penjualan.

**Halaman Riwayat Transaksi:**
- Tabel daftar semua transaksi (nomor urut, waktu, item yang dibeli, total)
- Filter berdasarkan event
- Filter berdasarkan tanggal
- Menampilkan maksimal 200 transaksi terbaru (ada notifikasi jika data terpotong)
- Klik **"Lihat"** → buka modal detail transaksi

**Modal Detail Transaksi:**
- Tampilkan detail item + total
- Tombol **"Edit Struk"**: ubah qty per item
  - Set qty ke 0 → item dihapus dari struk
  - Stok otomatis dikoreksi (stok lama dikembalikan, stok baru dipotong)
  - Total transaksi diperbarui otomatis
- Tombol **"Hapus Struk"**: hapus transaksi beserta file PNG
  - Stok semua item dalam transaksi **dikembalikan penuh**
  - Konfirmasi sebelum hapus

**Halaman Rekap Harian:**
- Pilih tanggal → lihat ringkasan:
  - Total omset hari itu
  - Jumlah transaksi
  - Rata-rata transaksi
  - Top 5 item terlaris
- Bisa filter per event

---

## 4. Alur Bisnis

```
[Pra-Event]
    Admin buat event baru
        ↓
    Admin input menu + stok
        ↓ (event dimulai)
[Saat Event]
    Kasir buka POS → pilih event aktif
        ↓
    Pelanggan datang → kasir tap item
        ↓ (jika stok tidak cukup → error ditampilkan)
    Kasir tap "Buat Struk" → PNG terdownload (dengan logo)
        ↓
    Stok otomatis berkurang
        ↓ (jika ada kesalahan input)
[Koreksi]
    Admin buka Rekap → Lihat → Edit atau Hapus struk
        ↓ (stok otomatis dikoreksi)
[Pasca-Event]
    Admin lihat rekap / riwayat
        ↓
    Admin hapus event (semua file PNG ikut terhapus)
```

---

## 5. Aturan Bisnis (Business Rules)

1. **Stok = 0 → Tidak bisa dijual.** Item dengan stok 0 tampil disabled.
2. **Qty melebihi stok → error eksplisit.** Tidak ada silent clamp qty.
3. **Stok tidak bisa minus.**
4. **Setiap transaksi mengurangi stok secara real-time.**
5. **Edit struk → stok dikoreksi atomik** (stok lama dikembalikan dahulu, stok baru dipotong).
6. **Hapus struk → stok dikembalikan penuh + file PNG dihapus dari disk.**
7. **Hapus event → semua file PNG struk event tersebut dihapus dari disk.**
8. **Nomor transaksi unik** berbasis UUID (`TRX-YYYYMMDD-XXXXXX`) — tidak ada konflik meski dua kasir checkout bersamaan.
9. **Tidak ada perhitungan pajak (PPN/service charge).**
10. **Tidak ada perhitungan diskon/promo.**

---

## 6. Hak Akses & Role

| Role | Akses |
|---|---|
| **Admin** | — CRUD event<br>— CRUD menu + stok<br>— Lihat riwayat transaksi<br>— Lihat rekap omset harian<br>— **Edit & hapus struk (dengan koreksi stok)** |
| **Kasir** | — Akses POS (transaksi)<br>— Generate & download struk |

> **Catatan:** Aplikasi hanya digunakan oleh satu usaha. 1 akun admin (dengan password). Mode kasir tidak memerlukan login.

---

## 7. Tampilan & UX

| Device Target | Spesifikasi |
|---|---|
| **Utama** | Tablet 7–10 inch (landscape diutamakan untuk POS) |
| **Desktop** | Oke, tapi prioritas tablet |
| **HP** | Tidak diutamakan |

**Responsivitas tablet (implementasi Tailwind CSS):**
- Cart panel POS: `w-60` (portrait) → `w-72` (landscape tablet) → `w-80` (desktop)
- Menu grid POS: 2 kolom (portrait) → 3 kolom (md:768px+) → 4 kolom (lg:1024px+)
- Tombol qty +/−: minimal 36×36 px (touch-friendly)
- Semua tabel admin: `overflow-x-auto` untuk scroll horizontal di layar kecil

**Prinsip desain:**
- Logo usaha di header semua halaman
- Minimalis, bersih, white/light background
- Warna aksen: hangat/cokelat (brand Dapoerasatoe)
- Tombol besar (finger-friendly, min 36×36 px)
- Font ukuran nyaman dibaca di tablet
- Loading state yang jelas (spinner/notif)
- Tailwind CSS + Alpine.js

---

## 8. Tech Stack (Implementasi)

| Layer | Teknologi | Versi |
|---|---|---|
| **Backend** | Python FastAPI | 0.115.5 |
| **ORM** | SQLAlchemy | 2.0.36 |
| **Template Engine** | Jinja2 | 3.1.4 |
| **Frontend** | Tailwind CSS (CDN) + Alpine.js 3.x | — |
| **Database (Dev)** | SQLite | built-in |
| **Database (Prod)** | PostgreSQL via Railway | — |
| **PNG Generator** | Pillow | 11.1.0 |
| **Server** | Uvicorn | 0.34.0 |
| **Session** | Starlette SessionMiddleware (itsdangerous) | 2.2.0 |
| **Hosting** | Railway.app | — |

---

## 9. Struktur Halaman

```
/                         → Landing: pilih role (Admin / Kasir)
/login                    → Login admin (password)
/admin/events             → Daftar event + CRUD
/admin/events/{id}        → Detail event (kelola menu item)
/admin/rekap              → Riwayat transaksi + rekap omset + edit/hapus struk
/kasir                    → Pilih event aktif
/kasir/pos/{event_id}     → POS utama (grid menu + keranjang)

API Endpoints:
GET  /api/events/{id}/menu-items    → Ambil menu + stok (untuk refresh POS)
POST /api/transactions              → Buat transaksi baru
GET  /admin/api/transactions/{id}   → Detail transaksi (untuk modal admin)
PUT  /admin/api/transactions/{id}   → Edit qty item transaksi
DELETE /admin/api/transactions/{id} → Hapus transaksi
GET  /struk/{filename}              → Download file PNG struk
```

---

## 10. Batasan (Out of Scope)

- ❌ Integrasi pembayaran (QRIS, kartu, tunai)
- ❌ Koneksi ke printer thermal
- ❌ Kirim struk via WhatsApp
- ❌ Pajak (PPN/service charge)
- ❌ Diskon / promo / voucher
- ❌ Multi-tenant
- ❌ Mode offline
- ❌ Export CSV/Excel
- ❌ Notifikasi suara

---

## 11. Keamanan

- Admin password di-set via environment variable (`ADMIN_PASSWORD`)
- `SECRET_KEY` untuk sesi cookie — **wajib diganti di production**
- Filename struk divalidasi dengan regex (`[A-Za-z0-9_\-]+\.png`) untuk mencegah path traversal
- HTML injection dicegah dengan Jinja2 autoescaping + data attribute pattern (tidak ada interpolasi string langsung ke JS)
- Konfirmasi sebelum hapus event/menu/transaksi

---

## 12. Deployment Guide — Railway.app

### 12.1 Prasyarat

- Akun [Railway.app](https://railway.app) (login via GitHub)
- Repo GitHub terhubung dengan Railway
- PostgreSQL plugin via Railway
- Volume (persistent storage) untuk file struk PNG

### 12.2 File Konfigurasi

**`Procfile`:**
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
```
> `--workers 1` wajib untuk SQLite. Jika PostgreSQL digunakan di production, bisa ditingkatkan.

**`nixpacks.toml`** — install font sistem:
```toml
[phases.setup]
nixPkgs = ["fonts-dejavu-core", "fonts-liberation"]
```

**`requirements.txt`** (versi yang digunakan):
```
fastapi==0.115.5
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
pillow==11.1.0
jinja2==3.1.4
python-multipart==0.0.32
itsdangerous==2.2.0
psycopg2-binary==2.9.10
```

### 12.3 Langkah Deploy

| Step | Tindakan |
|---|---|
| 1 | Push project ke GitHub (pastikan `logo_utama.jpeg` ikut ter-commit) |
| 2 | Railway → **New Project** → **Deploy from GitHub repo** |
| 3 | Tambah **PostgreSQL plugin** |
| 4 | Tambah **Volume**, mount ke `/app/app/static/struk` |
| 5 | Set env vars: `SECRET_KEY`, `ADMIN_PASSWORD`, `STRUK_DIR=/app/app/static/struk` |
| 6 | Railway build & deploy otomatis |
| 7 | Akses via domain `.railway.app` |

### 12.4 Environment Variables

| Variable | Nilai | Keterangan |
|---|---|---|
| `DATABASE_URL` | (auto dari PostgreSQL plugin) | Koneksi ke PostgreSQL |
| `STRUK_DIR` | `/app/app/static/struk` | Folder output struk PNG |
| `ADMIN_PASSWORD` | (set sendiri) | Password login admin |
| `SECRET_KEY` | (string acak 32+ karakter) | Key sesi — wajib diganti |
| `CASHIER_PASSCODE` | (opsional) | Passcode mode kasir |

### 12.5 Local vs Production

| Aspek | Local | Railway (Production) |
|---|---|---|
| Database | SQLite (`./kasir.db`) | PostgreSQL (managed) |
| Struk path | `./app/static/struk/` | Railway Volume mount |
| Run | `uvicorn app.main:app --reload` | `uvicorn ...` via Procfile |
| Env | `.env` file | Railway Variables |

---

**End of Document — v2.0**
