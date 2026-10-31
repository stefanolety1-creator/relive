import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

LOCAL_STORAGE_DIR = DATA_DIR / "storage"
LOCAL_STORAGE_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "live_accounts.db"

# Server Settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
SECRET_KEY = os.getenv("LIVE_SECRET_KEY", "windows-live-revival-secret-key-2026")
COOKIE_NAME = os.getenv("COOKIE_NAME", "WL_AUTH_TOKEN")
DOMAIN_SUFFIX = os.getenv("DOMAIN_SUFFIX", "@live.it")

# Google Drive configuration
GDRIVE_CREDENTIALS_FILE = BASE_DIR / "google_drive_credentials.json"
GDRIVE_ROOT_FOLDER_NAME = "Windows Live SkyDrive"
