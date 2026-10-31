@echo off
title Sblocco Accesso Windows Live Raccolta Foto
cd /d "C:\Users\stefanodeluca\.gemini\antigravity\scratch\windows-live-revival"

echo ======================================================
echo       SBLOCCO ACCESSO WINDOWS LIVE RACCOLTA FOTO
echo ======================================================
echo.
echo 1. Avvio di Raccolta Foto...
start "" "C:\Program Files (x86)\Windows Live\Photo Gallery\WLXPhotoGallery.exe"

echo 2. Avvio del monitor di sblocco...
echo    Non appena appare 'Accesso in corso...', verra' inviato
echo    automaticamente il segnale 0x8521 alla finestra!
echo.
".venv\Scripts\python.exe" login_watcher.py
