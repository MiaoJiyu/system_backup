"""Local file copy uploader."""
import os
import shutil
import logging
from client.src.upload.base import BaseUploader

logger = logging.getLogger(__name__)


class LocalUploader(BaseUploader):
    def validate_credential(self, credential: dict) -> bool:
        return "path" in credential

    def upload_file(self, local_path: str, remote_path: str, credential: dict) -> bool:
        try:
            dest_dir = credential["path"]
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, os.path.basename(local_path))

            file_size = os.path.getsize(local_path)
            logger.info(f"Copying {local_path} ({file_size} bytes) to {dest_path}")

            shutil.copy2(local_path, dest_path)
            logger.info(f"Local copy complete: {dest_path}")
            return True
        except Exception as e:
            logger.error(f"Local upload failed: {e}")
            return False
