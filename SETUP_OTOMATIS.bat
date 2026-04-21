@echo off
:: ============================================================
:: SETUP_OTOMATIS.bat — Konfigurasi Awal Sekali Jalan
:: Jalankan SEKALI sebagai Administrator untuk:
::   1. Daftarkan MySQL sebagai Windows Service (auto-start)
::   2. Buat shortcut "SIM Lab TJKT" di Desktop
::   3. Buat shortcut di Startup (agar otomatis saat login)
:: ============================================================
title Setup SIM Lab TJKT — Konfigurasi Otomatis

:: Cek hak Administrator
net session >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [!] File ini harus dijalankan sebagai Administrator!
    echo  [!] Klik kanan file ini lalu pilih "Run as administrator"
    echo.
    pause
    exit /b 1
)

cls
color 0B
echo.
echo  ============================================================
echo   SETUP OTOMATIS — SIM Lab TJKT
echo   SMKN 1 Cikarang Selatan
echo  ============================================================
echo.

:: ── LANGKAH 1: Temukan XAMPP ────────────────────────────────
set XAMPP=C:\xampp
if not exist "%XAMPP%\mysql\bin\mysqld.exe" set XAMPP=D:\xampp
if not exist "%XAMPP%\mysql\bin\mysqld.exe" set XAMPP=C:\XAMPP
if not exist "%XAMPP%\mysql\bin\mysqld.exe" (
    echo  [!] XAMPP tidak ditemukan. Install XAMPP dulu.
    pause & exit /b 1
)
echo  [1/4] XAMPP ditemukan di: %XAMPP%

:: ── LANGKAH 2: Daftarkan MySQL sebagai Windows Service ──────
echo  [2/4] Mendaftarkan MySQL sebagai Windows Service...
sc query MySQL >nul 2>&1
if errorlevel 1 (
    "%XAMPP%\mysql\bin\mysqld.exe" --install MySQL --defaults-file="%XAMPP%\mysql\bin\my.ini"
    net start MySQL
    echo        MySQL berhasil didaftarkan sebagai service.
    echo        MySQL akan otomatis menyala saat Windows booting.
) else (
    echo        MySQL service sudah terdaftar.
    net start MySQL >nul 2>&1
)
echo.

:: ── LANGKAH 3: Buat Shortcut di Desktop ─────────────────────
echo  [3/4] Membuat shortcut di Desktop...
set BAT_PATH=%~dp0JALANKAN.bat
set DESKTOP=%PUBLIC%\Desktop
set ICON_PATH=%~dp0static\img\icon_sekolah.ico

:: Konversi ikon PNG ke ICO jika belum ada
if not exist "%ICON_PATH%" (
    python "%~dp0convert_icon.py" >nul 2>&1
)

powershell -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $s  = $ws.CreateShortcut('%DESKTOP%\SIM Lab TJKT.lnk'); ^
   $s.TargetPath = '%BAT_PATH%'; ^
   $s.WorkingDirectory = '%~dp0'; ^
   $s.Description = 'SIM Lab TJKT - Sistem Inventaris Laboratorium TJKT'; ^
   if (Test-Path '%ICON_PATH%') { $s.IconLocation = '%ICON_PATH%' }; ^
   $s.Save()"

echo        Shortcut dibuat di Desktop semua pengguna.
echo.

:: ── LANGKAH 4: Buat Shortcut di Startup (Opsional) ──────────
echo  [4/4] Konfigurasi startup...
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

set /p AUTO="  Jalankan SIM Lab TJKT otomatis saat login Windows? (y/n): "
if /i "%AUTO%"=="y" (
    powershell -Command ^
      "$ws = New-Object -ComObject WScript.Shell; ^
       $s  = $ws.CreateShortcut('%STARTUP%\SIM Lab TJKT.lnk'); ^
       $s.TargetPath = '%BAT_PATH%'; ^
       $s.WorkingDirectory = '%~dp0'; ^
       $s.Description = 'SIM Lab TJKT - Auto Start'; ^
       if (Test-Path '%ICON_PATH%') { $s.IconLocation = '%ICON_PATH%' }; ^
       $s.Save()"
    echo        Sistem akan otomatis berjalan saat login.
) else (
    echo        Startup otomatis dilewati.
)
echo.

:: ── SELESAI ──────────────────────────────────────────────────
echo  ============================================================
echo   Setup selesai!
echo.
echo   Cara menggunakan setelah ini:
echo   1. MySQL sudah otomatis menyala saat Windows booting
echo   2. Klik dua kali "SIM Lab TJKT" di Desktop
echo   3. Browser akan terbuka otomatis ke http://127.0.0.1:5000
echo.
echo   Login: admin / admin123
echo  ============================================================
echo.
pause
