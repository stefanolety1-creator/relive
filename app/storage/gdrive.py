import io
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, BinaryIO, Optional
from datetime import datetime

from app.storage.base import StorageBackend
from app.config import GDRIVE_CREDENTIALS_FILE, GDRIVE_ROOT_FOLDER_NAME

logger = logging.getLogger("storage.gdrive")

try:
    from google.oauth2 import service_account, credentials as oauth_credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
    GDRIVE_AVAILABLE = True
except ImportError:
    GDRIVE_AVAILABLE = False

class GoogleDriveStorageBackend(StorageBackend):
    def __init__(self, credentials_path: Optional[Path] = None):
        if not GDRIVE_AVAILABLE:
            raise RuntimeError("Google API Client non e' installato (installa google-api-python-client e google-auth)")

        self.creds = self._load_credentials(credentials_path)
        self.service = build('drive', 'v3', credentials=self.creds)
        self.root_id = self._get_or_create_root_folder()
        logger.info(f"Google Drive Backend pronto! Root folder ID: {self.root_id}")

    def _load_credentials(self, credentials_path: Optional[Path] = None):
        scopes = ['https://www.googleapis.com/auth/drive']

        # 1. Check environment variable (utile per Render, Railway, cloud deploy)
        env_json = os.getenv("GDRIVE_CREDENTIALS_JSON")
        if env_json:
            try:
                info = json.loads(env_json)
                if "client_email" in info and "private_key" in info:
                    logger.info("Caricamento credenziali Google Drive da variabile d'ambiente (Service Account)...")
                    return service_account.Credentials.from_service_account_info(info, scopes=scopes)
                elif "token" in info or "refresh_token" in info:
                    logger.info("Caricamento credenziali Google Drive da variabile d'ambiente (OAuth2)...")
                    return oauth_credentials.Credentials.from_authorized_user_info(info, scopes=scopes)
            except Exception as e:
                logger.error(f"Errore parsing GDRIVE_CREDENTIALS_JSON: {e}")

        # 2. Check file paths
        candidate_paths = [
            credentials_path,
            GDRIVE_CREDENTIALS_FILE,
            Path("google_drive_credentials.json"),
            Path("credentials.json"),
            Path("data/google_drive_credentials.json"),
            Path("data/credentials.json")
        ]

        for p in candidate_paths:
            if p and Path(p).exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if "client_email" in data and "private_key" in data:
                        logger.info(f"Caricamento credenziali Google Drive da file: {p} (Service Account)")
                        return service_account.Credentials.from_service_account_file(str(p), scopes=scopes)
                    elif "token" in data or "refresh_token" in data:
                        logger.info(f"Caricamento credenziali Google Drive da file: {p} (OAuth2)")
                        return oauth_credentials.Credentials.from_authorized_user_info(data, scopes=scopes)
                    elif "installed" in data or "web" in data:
                        # OAuth client secrets file, prompt or load
                        logger.info(f"Rilevato client secrets Google OAuth2 in: {p}")
                        return service_account.Credentials.from_service_account_file(str(p), scopes=scopes)
                except Exception as e:
                    logger.warning(f"Errore caricamento da {p}: {e}")

        raise FileNotFoundError("Credenziali Google Drive non trovate in file o variabile d'ambiente GDRIVE_CREDENTIALS_JSON")

    def _get_or_create_root_folder(self) -> str:
        query = f"name = '{GDRIVE_ROOT_FOLDER_NAME}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        res = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = res.get('files', [])
        if files:
            return files[0]['id']
        
        meta = {
            'name': GDRIVE_ROOT_FOLDER_NAME,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = self.service.files().create(body=meta, fields='id').execute()
        return folder.get('id')

    def init_user_storage(self, user_email: str) -> str:
        # Check if user folder exists inside Windows Live SkyDrive
        safe_user_name = f"SkyDrive - {user_email}"
        query = f"'{self.root_id}' in parents and name = '{safe_user_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        res = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = res.get('files', [])
        if files:
            user_root_id = files[0]['id']
        else:
            meta = {
                'name': safe_user_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [self.root_id]
            }
            folder = self.service.files().create(body=meta, fields='id').execute()
            user_root_id = folder.get('id')

            # Create default folders
            for sub in ["Documenti", "Foto", "Pubblica", "Allegati Live Mail"]:
                sub_meta = {
                    'name': sub,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [user_root_id]
                }
                self.service.files().create(body=sub_meta, fields='id').execute()

        return user_root_id

    def list_items(self, user_email: str, parent_folder_id: str = "root") -> List[Dict[str, Any]]:
        user_root_id = self.init_user_storage(user_email)
        target_parent = user_root_id if parent_folder_id == "root" else parent_folder_id

        query = f"'{target_parent}' in parents and trashed = false"
        res = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType, size, modifiedTime)'
        ).execute()

        items = []
        for f in res.get('files', []):
            is_folder = (f.get('mimeType') == 'application/vnd.google-apps.folder')
            size_bytes = int(f.get('size', 0)) if not is_folder else 0
            
            raw_time = f.get('modifiedTime', '')
            formatted_time = ""
            if raw_time:
                try:
                    dt = datetime.fromisoformat(raw_time.replace('Z', '+00:00'))
                    formatted_time = dt.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    formatted_time = raw_time

            items.append({
                "id": f['id'],
                "name": f['name'],
                "is_folder": is_folder,
                "size_bytes": size_bytes,
                "mime_type": "folder" if is_folder else f.get('mimeType', 'application/octet-stream'),
                "modified": formatted_time,
                "parent_id": parent_folder_id
            })

        items.sort(key=lambda x: (not x["is_folder"], x["name"].lower()))
        return items

    def create_folder(self, user_email: str, folder_name: str, parent_folder_id: str = "root") -> Dict[str, Any]:
        user_root_id = self.init_user_storage(user_email)
        target_parent = user_root_id if parent_folder_id == "root" else parent_folder_id

        meta = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [target_parent]
        }
        f = self.service.files().create(body=meta, fields='id, name, mimeType, modifiedTime').execute()
        return {
            "id": f['id'],
            "name": f['name'],
            "is_folder": True,
            "size_bytes": 0,
            "mime_type": "folder",
            "modified": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "parent_id": parent_folder_id
        }

    def upload_file(self, user_email: str, file_name: str, file_stream: BinaryIO, mime_type: str, parent_folder_id: str = "root") -> Dict[str, Any]:
        user_root_id = self.init_user_storage(user_email)
        target_parent = user_root_id if parent_folder_id == "root" else parent_folder_id

        media = MediaIoBaseUpload(file_stream, mimetype=mime_type or 'application/octet-stream', resumable=True)
        meta = {
            'name': file_name,
            'parents': [target_parent]
        }
        f = self.service.files().create(body=meta, media_body=media, fields='id, name, mimeType, size, modifiedTime').execute()

        return {
            "id": f['id'],
            "name": f['name'],
            "is_folder": False,
            "size_bytes": int(f.get('size', 0)),
            "mime_type": f.get('mimeType', 'application/octet-stream'),
            "modified": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "parent_id": parent_folder_id
        }

    def get_file(self, user_email: str, file_id: str) -> Optional[tuple[BinaryIO, str, str]]:
        try:
            meta = self.service.files().get(fileId=file_id, fields='name, mimeType').execute()
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            fh.seek(0)
            return fh, meta['name'], meta.get('mimeType', 'application/octet-stream')
        except Exception:
            return None

    def delete_item(self, user_email: str, item_id: str) -> bool:
        try:
            self.service.files().delete(fileId=item_id).execute()
            return True
        except Exception:
            return False
