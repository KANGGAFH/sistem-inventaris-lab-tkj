@echo off
echo ===============================
echo SISTEM INVENTARIS LAB
echo ===============================

echo Menjalankan MySQL...
start "" "C:\xampp\mysql\bin\mysqld.exe"

timeout /t 5

echo Menjalankan Server Flask...
cd /d "D:\PROJEK KP2"

start python app.py

timeout /t 3

echo Membuka Browser...
start http://127.0.0.1:5000

exit