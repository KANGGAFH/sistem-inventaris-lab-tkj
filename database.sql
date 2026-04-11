-- ============================================================
-- DATABASE: Lab Inventory Management System v2.0
-- Lab     : Teknik Jaringan Komputer dan Telekomunikasi (TJKT)
-- ============================================================

CREATE DATABASE IF NOT EXISTS inventaris_lab
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE inventaris_lab;

-- ============================================================
-- TABLE: users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    username     VARCHAR(50)  NOT NULL UNIQUE,
    password     VARCHAR(255) NOT NULL,
    nama_lengkap VARCHAR(100) NOT NULL,
    email        VARCHAR(100),
    role         ENUM('admin','operator') DEFAULT 'admin',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO users (username, password, nama_lengkap, email, role) VALUES
('admin','$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW','Administrator','admin@smkn1cikarang.sch.id','admin');

-- ============================================================
-- TABLE: barang
-- Format kode: [PREFIX_KAT]-[PREFIX_TIPE]-[TAHUN]-[NOURUT]
-- Contoh     : KOM-COR-2024-0001
-- ============================================================
CREATE TABLE IF NOT EXISTS barang (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    kode_barang        VARCHAR(30)  NOT NULL UNIQUE,
    nama_barang        VARCHAR(150) NOT NULL,
    kategori           VARCHAR(50)  DEFAULT 'Komputer',
    tipe               VARCHAR(100),
    jenis_aset         ENUM('Aset Tetap','Aset Bergerak') DEFAULT 'Aset Tetap',
    spesifikasi        TEXT,
    kondisi            ENUM('Baik','Rusak Ringan','Rusak Berat') DEFAULT 'Baik',
    jumlah             INT          DEFAULT 1,
    tanggal_pengadaan  DATE,
    qr_path            VARCHAR(255),
    keterangan         TEXT,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: peminjaman
-- ============================================================
CREATE TABLE IF NOT EXISTS peminjaman (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    kode_pinjam         VARCHAR(25)  NOT NULL UNIQUE,
    barang_id           INT          NOT NULL,
    kode_barang         VARCHAR(30)  NOT NULL,
    nama_peminjam       VARCHAR(100) NOT NULL,
    kelas_jabatan       VARCHAR(50),
    no_hp               VARCHAR(20),
    keperluan           TEXT,
    jumlah_pinjam       INT          DEFAULT 1,
    tgl_pinjam          DATETIME     NOT NULL,               -- Tanggal + Jam pinjam
    tgl_kembali_rencana DATETIME     NOT NULL,               -- Rencana kembali: tanggal + jam
    tgl_kembali_aktual  DATETIME,                            -- Aktual kembali: tanggal + jam
    status              ENUM('Dipinjam','Dikembalikan','Terlambat') DEFAULT 'Dipinjam',
    kondisi_kembali     ENUM('Baik','Rusak Ringan','Rusak Berat'),
    catatan_admin       TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (barang_id) REFERENCES barang(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: riwayat_scan
-- ============================================================
CREATE TABLE IF NOT EXISTS riwayat_scan (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    barang_id   INT          NOT NULL,
    kode_barang VARCHAR(30)  NOT NULL,
    nama_barang VARCHAR(150),
    ip_scanner  VARCHAR(50),
    user_agent  TEXT,
    scanned_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (barang_id) REFERENCES barang(id) ON DELETE CASCADE
) ENGINE=InnoDB;


-- ============================================================
-- TABLE: barang_habis_pakai (Consumable Items)
-- Terpisah dari tabel barang utama karena logika berbeda:
-- barang ini memiliki stok yang berkurang saat dipakai
-- dan bisa di-restock kapan saja
-- ============================================================
CREATE TABLE IF NOT EXISTS barang_habis_pakai (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    kode_barang        VARCHAR(30)  NOT NULL UNIQUE,  -- Format: CSM-[KAT]-[TAHUN]-[NOURUT]
    nama_barang        VARCHAR(150) NOT NULL,
    kategori           VARCHAR(50)  DEFAULT 'Kabel & Konektor',
    satuan             VARCHAR(20)  DEFAULT 'pcs',    -- pcs, meter, roll, pack, box
    stok_awal          INT          DEFAULT 0,
    stok_sekarang      INT          DEFAULT 0,
    stok_minimum       INT          DEFAULT 5,        -- alert jika stok di bawah ini
    harga_satuan       DECIMAL(12,0) DEFAULT 0,
    lokasi_simpan      VARCHAR(100),
    qr_path            VARCHAR(255),                  -- Path file QR Code PNG
    keterangan         TEXT,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ALTER untuk database yang sudah ada:
-- ALTER TABLE barang_habis_pakai ADD COLUMN IF NOT EXISTS qr_path VARCHAR(255) AFTER lokasi_simpan;

-- ============================================================
-- TABLE: riwayat_stok (Log setiap perubahan stok)
-- Mencatat semua aktivitas: pemakaian, restock, koreksi
-- ============================================================
CREATE TABLE IF NOT EXISTS riwayat_stok (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    barang_id       INT          NOT NULL,
    kode_barang     VARCHAR(30)  NOT NULL,
    nama_barang     VARCHAR(150),
    tipe_transaksi  ENUM('Masuk','Keluar','Koreksi') NOT NULL,
    jumlah          INT          NOT NULL,
    stok_sebelum    INT          NOT NULL,
    stok_sesudah    INT          NOT NULL,
    nama_pemakai    VARCHAR(100),                     -- Nama guru/siswa yang menggunakan
    mata_pelajaran  VARCHAR(100),                     -- Mata pelajaran (opsional)
    kelas           VARCHAR(50),                      -- Kelas (opsional)
    keterangan      VARCHAR(255),
    dicatat_oleh    VARCHAR(100),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (barang_id) REFERENCES barang_habis_pakai(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ALTER untuk database yang sudah ada (jalankan jika tabel sudah terbuat sebelumnya)
-- ALTER TABLE riwayat_stok ADD COLUMN IF NOT EXISTS nama_pemakai VARCHAR(100) AFTER stok_sesudah;
-- ALTER TABLE riwayat_stok ADD COLUMN IF NOT EXISTS mata_pelajaran VARCHAR(100) AFTER nama_pemakai;
-- ALTER TABLE riwayat_stok ADD COLUMN IF NOT EXISTS kelas VARCHAR(50) AFTER mata_pelajaran;

-- Jika database sudah ada, jalankan ALTER ini di phpMyAdmin → SQL:
ALTER TABLE riwayat_stok
    ADD COLUMN IF NOT EXISTS nama_pemakai   VARCHAR(100) AFTER stok_sesudah,
    ADD COLUMN IF NOT EXISTS mata_pelajaran VARCHAR(100) AFTER nama_pemakai,
    ADD COLUMN IF NOT EXISTS kelas          VARCHAR(50)  AFTER mata_pelajaran;

