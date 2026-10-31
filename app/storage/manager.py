import os
import logging
from pathlib import Path
from app.config import GDRIVE_CREDENTIALS_FILE
from app.storage.base import StorageBackend
from app.storage.local import LocalStorageBackend
from app.storage.gdrive import GoogleDriveStorageBackend, GDRIVE_AVAILABLE

logger = logging.getLogger("windows_live")

_backend_instance: StorageBackend = None

def get_storage_backend() -> tuple[StorageBackend, str]:
    global _backend_instance
    if _backend_instance is not None:
        name = "Google Drive Cloud" if isinstance(_backend_instance, GoogleDriveStorageBackend) else "Storage Locale"
        return _backend_instance, name

    has_gdrive_config = (
        bool(os.getenv("GDRIVE_CREDENTIALS_JSON")) or
        GDRIVE_CREDENTIALS_FILE.exists() or
        Path("google_drive_credentials.json").exists() or
        Path("credentials.json").exists() or
        Path("data/credentials.json").exists()
    )

    if GDRIVE_AVAILABLE and has_gdrive_config:
        try:
            logger.info("Inizializzazione backend Google Drive...")
            _backend_instance = GoogleDriveStorageBackend()
            return _backend_instance, "Google Drive Cloud"
        except Exception as e:
            logger.warning(f"Errore inizializzazione Google Drive: {e}. Uso fallback locale.")

    logger.info("Uso backend di archiviazione locale (25 GB emulati).")
    _backend_instance = LocalStorageBackend()
    return _backend_instance, "Storage Locale"
