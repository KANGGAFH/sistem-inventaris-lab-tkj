@echo off
:: ============================================================
:: JALANKAN.bat — SIM Lab TJKT
:: Klik dua kali file ini untuk menjalankan sistem
:: ============================================================
title SIM Lab TJKT — Menjalankan Sistem...
color 0A
cls

echo.
echo  ============================================================
echo   SIM Lab TJKT — Sistem Inventaris Laboratorium TJKT
echo   SMKN 1 Cikarang Selatan
echo  ============================================================
echo.
echo  Sedang mempersiapkan sistem, mohon tunggu...
echo.

:: ── LANGKAH 1: Pastikan XAMPP MySQL sudah berjalan ──────────
echo  [1/4] Memeriksa status MySQL...

:: Cek apakah MySQL sudah running
sc query mysql >nul 2>&1
if %errorlevel% == 0 (
    echo        MySQL service terdeteksi.
    net start mysql >nul 2>&1
    goto MYSQL_OK
)

:: Coba start MySQL via XAMPP
set XAMPP_DIR=C:\xampp
if not exist "%XAMPP_DIR%\mysql\bin\mysqld.exe" set XAMPP_DIR=D:\xampp
if not exist "%XAMPP_DIR%\mysql\bin\mysqld.exe" set XAMPP_DIR=C:\XAMPP
if not exist "%XAMPP_DIR%\mysql\bin\mysqld.exe" (
    echo.
    echo  [!] XAMPP tidak ditemukan di C:\xampp atau D:\xampp
    echo  [!] Silakan start MySQL manual lewat XAMPP Control Panel
    echo      lalu klik dua kali file ini lagi.
    echo.
    pause
    exit /b 1
)

echo        Memulai MySQL via XAMPP...
start "" "%XAMPP_DIR%\mysql\bin\mysqld.exe" --defaults-file="%XAMPP_DIR%\mysql\bin\my.ini"
timeout /t 3 /nobreak >nul

:MYSQL_OK
echo        MySQL siap.
echo.

:: ── LANGKAH 2: Cek Python ───────────────────────────────────
echo  [2/4] Memeriksa Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [!] Python tidak ditemukan!
    echo  [!] Install Python dari https://python.org/downloads
    echo      Centang "Add Python to PATH" saat instalasi.
    echo.
    pause
    exit /b 1
)
echo        Python siap.
echo.

:: ── LANGKAH 3: Pindah ke folder proyek ──────────────────────
echo  [3/4] Memuat aplikasi...
:: Pindah ke folder tempat file .bat ini berada
cd /d "%~dp0"
echo        Folder: %~dp0
echo.

:: ── LANGKAH 4: Jalankan Flask dan buka browser ──────────────
echo  [4/4] Menjalankan server...
echo.
echo  ============================================================
echo   Sistem berhasil dijalankan!
echo.
echo   Buka browser dan akses:
echo   http://127.0.0.1:5000
echo.
echo   Untuk akses dari HP (WiFi sama):
echo   Lihat alamat IP di bawah ini:
ipconfig | findstr "IPv4"
echo.
echo   JANGAN tutup jendela ini selama sistem digunakan!
echo  ============================================================
echo.


:: Jalankan Flask (gunakan launcher GUI jika ada, fallback ke app.py)
if exist "launcher.py" (
    python launcher.py
) else (
    python app.py
)

:: Jika Flask berhenti / error
echo.
echo  [!] Server berhenti. Tekan tombol apa saja untuk keluar.
pause >nul
