# 🖥️ SIM Lab Komputer — Sistem Inventaris Laboratorium
**Proyek Kerja Praktek (KP) | Python Flask + MySQL + Bootstrap 5**

---

## 📁 Struktur Folder

```
lab_inventory/
│
├── app.py                  # Backend Flask (entry point)
├── requirements.txt        # Python dependencies
├── database.sql            # Script SQL database
├── README.md               # Dokumentasi ini
│
├── templates/              # Halaman HTML (Jinja2)
│   ├── base.html           # Layout utama (sidebar + navbar)
│   ├── login.html          # Halaman login
│   ├── dashboard.html      # Dashboard & statistik
│   ├── barang.html         # Tabel inventaris + search + pagination
│   ├── barang_form.html    # Form tambah/edit barang
│   ├── detail.html         # Halaman detail (target scan QR)
│   ├── scanner.html        # Halaman scan QR via kamera
│   ├── riwayat.html        # Riwayat scan QR
│   └── 404.html            # Error page
│
└── static/
    ├── css/
    │   └── style.css       # Stylesheet utama
    ├── js/
    │   └── main.js         # JavaScript global
    └── qr/                 # QR Code yang di-generate (auto)
```

---

## ⚙️ Cara Menjalankan

### 1. Persiapan
- Install **XAMPP** dan jalankan **Apache + MySQL**
- Install **Python 3.9+**

### 2. Setup Database
Buka **phpMyAdmin** (`http://localhost/phpmyadmin`), lalu:
1. Klik **"New"** → buat database `lab_inventory`
2. Import file `database.sql` (Menu **Import** → pilih file)

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

> Jika error `mysqlclient`, coba:
> - Windows: `pip install mysqlclient` (pastikan sudah install Visual C++ Build Tools)
> - Alternatif: ganti `Flask-MySQLdb` dengan `Flask-MySQL` atau gunakan `PyMySQL`

### 4. Jalankan Aplikasi
```bash
python app.py
```

Akses di browser: **http://localhost:5000**

---

## 📱 Akses dari HP (Jaringan Lokal)

### Langkah:
1. Pastikan HP dan komputer terhubung ke **WiFi yang sama**
2. Cari IP komputer:
   - Windows: `ipconfig` → lihat **IPv4 Address** (misal: `192.168.1.5`)
   - Linux/Mac: `ifconfig` atau `ip addr`
3. Akses dari HP: **http://192.168.1.5:5000**

### Untuk QR Code yang bisa di-scan dari HP:
Edit `app.py`, pada fungsi `buat_qr_code()`, ganti:
```python
qr_data = f"http://[IP_KOMPUTER]:5000/barang/detail/{kode_barang}"
```
Menjadi (sesuai IP komputer Anda):
```python
qr_data = f"http://192.168.1.5:5000/barang/detail/{kode_barang}"
```

---

## 🔐 Akun

| Username | Password |
|----------|----------|
| admin    | admin123 |

> **Catatan:** Password `admin123` di database.sql sudah berbentuk bcrypt hash.
> Untuk generate hash baru, jalankan di Python:
> ```python
> import bcrypt
> hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
> print(hash)
> ```

---

## ✨ Fitur Sistem

| Fitur | Keterangan |
|-------|-----------|
| 🔐 Login | Autentikasi dengan bcrypt, session Flask |
| 📊 Dashboard | Statistik total, kondisi, chart kategori & kondisi |
| 📋 Inventaris | CRUD barang, search, pagination, filter |
| 📱 QR Code | Generate otomatis saat tambah barang |
| 🔍 Scan QR | Scan dari kamera HP langsung di browser |
| 📄 Detail | Halaman detail barang setelah scan |
| 🕒 Riwayat | Log setiap kali QR di-scan |

---

## 🛠️ Teknologi

- **Backend:** Python 3.x + Flask 3.0
- **Database:** MySQL (XAMPP)
- **Frontend:** HTML5 + CSS3 + Bootstrap 5.3
- **QR Generator:** qrcode (Python library)
- **QR Scanner:** html5-qrcode (JavaScript)
- **Charts:** Chart.js 4.x
- **Icons:** Bootstrap Icons 1.11
- **Font:** Plus Jakarta Sans + JetBrains Mono

---

## 📝 Catatan Pengembangan

- Pastikan folder `static/qr/` memiliki permission write
- QR Code disimpan di `static/qr/qr_<kode_barang>.png`
- URL QR harus disesuaikan dengan IP komputer untuk scan dari HP
- Gunakan `app.run(host='0.0.0.0')` agar bisa diakses dari jaringan lokal

---

*© 2024 SIM Lab Komputer — Proyek Kerja Praktek*
