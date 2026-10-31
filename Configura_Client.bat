@echo off
title Configurazione Client Windows Live Revival
color 0b

:: Verifica privilegi di amministratore
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Richiesta permessi di amministratore...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo =====================================================================
echo          CONFIGURAZIONE CLIENT WINDOWS LIVE REVIVAL
echo =====================================================================
echo.
echo Questo script colleghera' il tuo PC al Server Windows Live Revival.
echo.
echo Scegli una delle seguenti opzioni:
echo   [1] Connetti a Server Locale (127.0.0.1)
echo   [2] Connetti a Server Remoto (Inserisci IP o Dominio del Server)
echo   [3] Ripristina file hosts originale (Rimuovi reindirizzamenti)
echo.
set /p SCELTA="Digita 1, 2 o 3 e premi Invio: "

set HOSTS_FILE=%windir%\System32\drivers\etc\hosts

if "%SCELTA%"=="1" (
    set SERVER_IP=127.0.0.1
    goto APPLICA
)

if "%SCELTA%"=="2" (
    set /p SERVER_IP="Inserisci l'indirizzo IP del Server Remoto: "
    goto APPLICA
)

if "%SCELTA%"=="3" (
    goto RIPRISTINA
)

echo Scelta non valida.
pause
exit /b

:APPLICA
echo.
echo Configurazione in corso con IP: %SERVER_IP%...

:: Rimuovi vecchie voci
powershell -Command "(Get-Content '%HOSTS_FILE%') | Where-Object { $_ -notmatch 'login.live.com|nexus.passport.com|spaces.live.com|byrdr.livefilestore.com|storage.live.com|storage.msn.com|contacts.msn.com|directory.services.live.com' } | Set-Content '%HOSTS_FILE%'"

:: Aggiungi nuove voci
echo. >> "%HOSTS_FILE%"
echo # Windows Live Revival Server >> "%HOSTS_FILE%"
echo %SERVER_IP% login.live.com >> "%HOSTS_FILE%"
echo %SERVER_IP% nexus.passport.com >> "%HOSTS_FILE%"
echo %SERVER_IP% spaces.live.com >> "%HOSTS_FILE%"
echo %SERVER_IP% byrdr.livefilestore.com >> "%HOSTS_FILE%"
echo %SERVER_IP% storage.live.com >> "%HOSTS_FILE%"
echo %SERVER_IP% storage.msn.com >> "%HOSTS_FILE%"
echo %SERVER_IP% contacts.msn.com >> "%HOSTS_FILE%"
echo %SERVER_IP% directory.services.live.com >> "%HOSTS_FILE%"

:: Installa certificato SSL se presente nella cartella
if exist "%~dp0certs\live_revival.crt" (
    echo Installazione certificato SSL di sicurezza...
    certutil.exe -addstore -f Root "%~dp0certs\live_revival.crt" >nul
)

ipconfig /flushdns >nul
echo.
echo =====================================================================
echo  Configurazione completata con successo!
echo  Ora puoi avviare Raccolta Foto ed accedere con il tuo account!
echo =====================================================================
echo.
pause
exit /b

:RIPRISTINA
echo.
echo Ripristino file hosts...
powershell -Command "(Get-Content '%HOSTS_FILE%') | Where-Object { $_ -notmatch 'login.live.com|nexus.passport.com|spaces.live.com|byrdr.livefilestore.com|storage.live.com|storage.msn.com|contacts.msn.com|directory.services.live.com|Windows Live Revival' } | Set-Content '%HOSTS_FILE%'"
ipconfig /flushdns >nul
echo File hosts ripristinato.
pause
exit /b
