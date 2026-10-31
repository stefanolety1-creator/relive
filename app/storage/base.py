from abc import ABC, abstractmethod
from typing import List, Dict, Any, BinaryIO, Optional

class StorageBackend(ABC):
    @abstractmethod
    def init_user_storage(self, user_email: str) -> str:
        """Initialize user root directory/folder and default subfolders (Documenti, Foto, Pubblica)"""
        pass

    @abstractmethod
    def list_items(self, user_email: str, parent_folder_id: str = "root") -> List[Dict[str, Any]]:
        """List files and folders in the specified folder"""
        pass

    @abstractmethod
    def create_folder(self, user_email: str, folder_name: str, parent_folder_id: str = "root") -> Dict[str, Any]:
        """Create a new folder"""
        pass

    @abstractmethod
    def upload_file(self, user_email: str, file_name: str, file_stream: BinaryIO, mime_type: str, parent_folder_id: str = "root") -> Dict[str, Any]:
        """Upload a file"""
        pass

    @abstractmethod
    def get_file(self, user_email: str, file_id: str) -> Optional[tuple[BinaryIO, str, str]]:
        """Retrieve file (stream, filename, mime_type)"""
        pass

    @abstractmethod
    def delete_item(self, user_email: str, item_id: str) -> bool:
        """Delete file or folder"""
        pass
