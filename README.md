# ReLive — Windows Live Essentials Wave 3 Revival Server

<p align="center">
  <img src="https://raw.githubusercontent.com/stefanolety1-creator/relive/main/app/static/img/banner.png" alt="ReLive Banner" width="600" onerror="this.style.display='none'"/>
</p>

**ReLive** è un server revival open-source centralizzato progettato per far rivivere la suite **Windows Live Essentials Wave 3 (2009)**.

---

## 🌟 Funzionalità Principali

* **🔑 Windows Live ID (Passport WS-Trust):** Emulazione autentica SOAP WS-Trust RST2 per `login.live.com` con emissione di ticket di identità e PUID.
* **📷 Raccolta Foto (Photo Gallery):** Accesso autentico client-side, download delle impostazioni da `spaces.live.com/wlpg.aspx` e pubblicazione album.
* **☁️ SkyDrive Cloud (Google Drive API):** Archiviazione fino a 25 GB per ogni utente registrato, con sincronizzazione trasparente su Google Drive.
* **✉️ Windows Live Mail & DeltaSync:** Server DeltaSync e SMTP per inviare e ricevere posta con supporto all'inoltro verso la tua casella reale (Gmail, Outlook, ecc.).
* **✍️ Windows Live Writer:** Supporto MetaWeblog API con Really Simple Discovery (RSD).
* **💬 Partner con Escargot Chat:** Reindirizzamento dedicato a [Escargot Chat](https://escargot.chat) per la messaggistica istantanea (MSN / Windows Live Messenger).

---

## 🚀 Deploy Gratuito su Render.com con 1 Clic

1. Crea un account su [Render.com](https://render.com) e accedi con GitHub.
2. Clicca su **New +** &rarr; **Web Service**.
3. Seleziona questo repository (`relive`).
4. Render leggerà automaticamente il file `render.yaml`:
   * **Runtime:** Python 3
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Clicca su **Deploy Web Service**!

---

## 💻 Come connettere il client Windows

1. Scarica ed esegui `Configura_Client.bat` con diritti di amministratore.
2. Scegli se connetterti al server in locale (`127.0.0.1`) o inserire l'indirizzo del tuo server remoto Render.
3. Avvia Windows Live Raccolta Foto ed effettua l'accesso!

---

## 🛡️ Licenza e Disclaimer
Tutti i marchi e nomi commerciali citati appartengono a Microsoft Corporation. ReLive è un progetto no-profit della community creato a scopo di preservazione storica del software.
