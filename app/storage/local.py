import os
import shutil
import uuid
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, BinaryIO, Optional
from datetime import datetime

from app.storage.base import StorageBackend
from app.config import LOCAL_STORAGE_DIR

class LocalStorageBackend(StorageBackend):
    def __init__(self, root_dir: Path = LOCAL_STORAGE_DIR):
        self.root_dir = root_dir
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _get_user_dir(self, user_email: str) -> Path:
        safe_name = user_email.replace("@", "_at_").replace(".", "_")
        user_dir = self.root_dir / safe_name
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def init_user_storage(self, user_email: str) -> str:
        user_dir = self._get_user_dir(user_email)
        # Default retro SkyDrive folders
        default_folders = ["Documenti", "Foto", "Pubblica", "Allegati Live Mail"]
        for folder in default_folders:
            (user_dir / folder).mkdir(exist_ok=True)
        return "root"

    def _resolve_path(self, user_email: str, folder_id: str) -> Path:
        user_dir = self._get_user_dir(user_email)
        if folder_id == "root" or not folder_id:
            return user_dir
        target = user_dir / folder_id
        if not target.resolve().is_relative_to(user_dir.resolve()):
            raise PermissionError("Path traversal detected")
        return target

    def list_items(self, user_email: str, parent_folder_id: str = "root") -> List[Dict[str, Any]]:
        self.init_user_storage(user_email)
        folder_path = self._resolve_path(user_email, parent_folder_id)
        if not folder_path.exists():
            return []

        user_dir = self._get_user_dir(user_email)
        items = []
        for entry in os.scandir(folder_path):
            is_dir = entry.is_dir()
            stat = entry.stat()
            rel_path = Path(entry.path).relative_to(user_dir).as_posix()
            
            mime_type = "folder" if is_dir else (mimetypes.guess_type(entry.name)[0] or "application/octet-stream")
            items.append({
                "id": rel_path,
                "name": entry.name,
                "is_folder": is_dir,
                "size_bytes": 0 if is_dir else stat.st_size,
                "mime_type": mime_type,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
                "parent_id": parent_folder_id
            })
        
        # Sort folders first, then alphabetically
        items.sort(key=lambda x: (not x["is_folder"], x["name"].lower()))
        return items

    def create_folder(self, user_email: str, folder_name: str, parent_folder_id: str = "root") -> Dict[str, Any]:
        parent_path = self._resolve_path(user_email, parent_folder_id)
        # Clean folder name
        safe_name = "".join(c for c in folder_name if c.isalnum() or c in (" ", "_", "-")).strip()
        if not safe_name:
            safe_name = "Nuova cartella"
        
        target = parent_path / safe_name
        counter = 1
        orig_name = safe_name
        while target.exists():
            safe_name = f"{orig_name} ({counter})"
            target = parent_path / safe_name
            counter += 1

        target.mkdir(parents=True, exist_ok=True)
        user_dir = self._get_user_dir(user_email)
        rel_path = target.relative_to(user_dir).as_posix()
        return {
            "id": rel_path,
            "name": safe_name,
            "is_folder": True,
            "size_bytes": 0,
            "mime_type": "folder",
            "modified": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "parent_id": parent_folder_id
        }

    def upload_file(self, user_email: str, file_name: str, file_stream: BinaryIO, mime_type: str, parent_folder_id: str = "root") -> Dict[str, Any]:
        parent_path = self._resolve_path(user_email, parent_folder_id)
        safe_name = Path(file_name).name
        target = parent_path / safe_name

        with open(target, "wb") as f:
            shutil.copyfileobj(file_stream, f)

        user_dir = self._get_user_dir(user_email)
        rel_path = target.relative_to(user_dir).as_posix()
        stat = target.stat()
        return {
            "id": rel_path,
            "name": safe_name,
            "is_folder": False,
            "size_bytes": stat.st_size,
            "mime_type": mime_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream",
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
            "parent_id": parent_folder_id
        }

    def get_file(self, user_email: str, file_id: str) -> Optional[tuple[BinaryIO, str, str]]:
        file_path = self._resolve_path(user_email, file_id)
        if not file_path.exists() or file_path.is_dir():
            return None
        
        mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        return open(file_path, "rb"), file_path.name, mime_type

    def delete_item(self, user_email: str, item_id: str) -> bool:
        item_path = self._resolve_path(user_email, item_id)
        if not item_path.exists():
            return False
        if item_path.is_dir():
            shutil.rmtree(item_path)
        else:
            item_path.unlink()
        return True
