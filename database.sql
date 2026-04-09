-- ============================================================
-- DATABASE: Lab Inventory Management System v2.0
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
('admin','$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW','Administrator','adminsmkn1bekasi.sch.id','admin'); -- plain password adalah "secret"

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
