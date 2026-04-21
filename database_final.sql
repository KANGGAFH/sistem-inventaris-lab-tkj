-- ============================================================
-- DATABASE: Lab Inventory Management System v3.1
-- Sekolah : SMKN 1 Cikarang Selatan, Bekasi
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
    has_unit_tracking  TINYINT(1)   DEFAULT 0
        COMMENT '1 jika barang ini menggunakan tracking per unit fisik',
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: barang_unit
-- Untuk barang yang setiap unitnya perlu dilacak terpisah
-- Contoh: Tablet, Laptop, Kamera — bukan Mouse atau Kabel
-- ============================================================
CREATE TABLE IF NOT EXISTS barang_unit (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    barang_id    INT          NOT NULL,
    kode_unit    VARCHAR(40)  NOT NULL UNIQUE,  -- TAB-2024-0001-U01
    nomor_unit   VARCHAR(20)  NOT NULL,          -- "1", "2", "10"
    label_unit   VARCHAR(100) NULL,              -- Label bebas, misal "Tab Kelas A"
    kondisi      ENUM('Baik','Rusak Ringan','Rusak Berat') DEFAULT 'Baik',
    status       ENUM('Tersedia','Dipinjam') DEFAULT 'Tersedia',
    qr_path      VARCHAR(255) NULL,
    keterangan   TEXT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (barang_id) REFERENCES barang(id) ON DELETE CASCADE
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ============================================================
-- TABLE: peminjaman
-- ============================================================
CREATE TABLE IF NOT EXISTS peminjaman (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    kode_pinjam           VARCHAR(25)  NOT NULL UNIQUE,
    barang_id             INT          NULL,
    kode_barang           VARCHAR(30)  NOT NULL,
    nama_barang_snapshot  VARCHAR(150) NULL,
    nama_peminjam         VARCHAR(100) NOT NULL,
    kelas_jabatan         VARCHAR(50),
    no_hp                 VARCHAR(20),
    keperluan             TEXT,
    jumlah_pinjam         INT          DEFAULT 1,
    unit_id               INT          NULL
        COMMENT 'FK ke barang_unit, NULL jika tidak pakai unit tracking',
    kode_unit             VARCHAR(40)  NULL
        COMMENT 'Snapshot kode unit saat dipinjam',
    tgl_pinjam            DATETIME     NOT NULL,
    tgl_kembali_rencana   DATETIME     NOT NULL,
    tgl_kembali_aktual    DATETIME,
    status                ENUM('Dipinjam','Dikembalikan','Terlambat') DEFAULT 'Dipinjam',
    kondisi_kembali       ENUM('Baik','Rusak Ringan','Rusak Berat'),
    catatan_admin         TEXT,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (barang_id) REFERENCES barang(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: riwayat_scan
-- ============================================================
CREATE TABLE IF NOT EXISTS riwayat_scan (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    barang_id   INT          NULL,
    kode_barang VARCHAR(30)  NOT NULL,
    nama_barang VARCHAR(150),
    ip_scanner  VARCHAR(50),
    user_agent  TEXT,
    scanned_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (barang_id) REFERENCES barang(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: barang_habis_pakai (Consumable Items)
-- ============================================================
CREATE TABLE IF NOT EXISTS barang_habis_pakai (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    kode_barang        VARCHAR(30)  NOT NULL UNIQUE,
    nama_barang        VARCHAR(150) NOT NULL,
    kategori           VARCHAR(50)  DEFAULT 'Kabel & Konektor',
    satuan             VARCHAR(20)  DEFAULT 'pcs',
    stok_awal          INT          DEFAULT 0,
    stok_sekarang      INT          DEFAULT 0,
    stok_minimum       INT          DEFAULT 5,
    harga_satuan       DECIMAL(12,0) DEFAULT 0,
    lokasi_simpan      VARCHAR(100),
    qr_path            VARCHAR(255),
    keterangan         TEXT,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: riwayat_stok
-- ============================================================
CREATE TABLE IF NOT EXISTS riwayat_stok (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    barang_id       INT          NULL,
    kode_barang     VARCHAR(30)  NOT NULL,
    nama_barang     VARCHAR(150),
    tipe_transaksi  ENUM('Masuk','Keluar','Koreksi') NOT NULL,
    jumlah          INT          NOT NULL,
    stok_sebelum    INT          NOT NULL,
    stok_sesudah    INT          NOT NULL,
    nama_pemakai    VARCHAR(100),
    mata_pelajaran  VARCHAR(100),
    kelas           VARCHAR(50),
    keterangan      VARCHAR(255),
    dicatat_oleh    VARCHAR(100),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (barang_id) REFERENCES barang_habis_pakai(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================================
-- VERIFIKASI
-- ============================================================
SELECT 'Database inventaris_lab berhasil dibuat!' AS status;
SELECT COUNT(*) AS jumlah_tabel
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'inventaris_lab';
