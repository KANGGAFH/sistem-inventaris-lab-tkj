-- ============================================================
-- DATABASE: Lab Inventory Management System
-- Sekolah  : SMKN 1 Cikarang Selatan, Bekasi
-- Jurusan  : Teknik Jaringan Komputer dan Telekomunikasi
-- Dibuat untuk: Kerja Praktek (KP) | Versi 2.0
-- ============================================================

CREATE DATABASE IF NOT EXISTS inventory_tkj CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE inventory_tkj;

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
('admin','$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW','Administrator','admin@smkn1bekasi.sch.id','admin');

-- ============================================================
-- TABLE: barang
-- Kode format: [PREFIX_KATEGORI]-[PREFIX_TIPE]-[TAHUN]-[NOURUT]
-- Contoh     : KOM-DES-2024-0001
-- ============================================================
CREATE TABLE IF NOT EXISTS barang (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    kode_barang       VARCHAR(30)  NOT NULL UNIQUE,
    nama_barang       VARCHAR(150) NOT NULL,
    kategori          VARCHAR(50)  NOT NULL DEFAULT 'Komputer',
    tipe_barang       VARCHAR(50)  NOT NULL DEFAULT 'Desktop',
    merk              VARCHAR(100),
    spesifikasi       TEXT,
    kondisi           ENUM('Baik','Rusak Ringan','Rusak Berat') DEFAULT 'Baik',
    jumlah            INT  DEFAULT 1,
    tanggal_pengadaan DATE,
    qr_path           VARCHAR(255),
    keterangan        TEXT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: riwayat_scan
-- ============================================================
CREATE TABLE IF NOT EXISTS riwayat_scan (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    barang_id   INT  NOT NULL,
    kode_barang VARCHAR(30) NOT NULL,
    nama_barang VARCHAR(150),
    ip_scanner  VARCHAR(50),
    user_agent  TEXT,
    scanned_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (barang_id) REFERENCES barang(id) ON DELETE CASCADE
) ENGINE=InnoDB;
