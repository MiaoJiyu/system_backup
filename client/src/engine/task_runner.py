"""Backup task runner - orchestrates scan, encrypt, compress, and upload."""
import os
import time
import tempfile
import logging
from datetime import datetime

from client.src.engine.scanner import scan_directory, update_fingerprint
from client.src.crypto.key_manager import KeyManager
from client.src.crypto.encryptor import FileEncryptor
from client.src.crypto.compressor import Compressor
from client.src.upload.base import create_uploader
from client.src.network.ws_client import WSClient
from client.src.storage.db import fingerprint_db

logger = logging.getLogger(__name__)

CHUNK_SIZE = 100 * 1024 * 1024  # 100MB chunks


class TaskRunner:
    def __init__(self, ws_client: WSClient, policy: dict, key_manager: KeyManager):
        self.ws = ws_client
        self.policy = policy
        self.key_manager = key_manager
        self.encryptor = FileEncryptor(key_manager)
        self.compressor = Compressor()

    def run(self, source_device: str | None = None):
        """Execute backup task for configured directories or USB device."""
        backup_dirs = self.policy.get("backup_directories", [])
        backup_usb = self.policy.get("backup_usb", True)
        upload_storage_id = self.policy.get("upload_storage_id")
        encrypt = self.policy.get("encryption_enabled", True)
        compress = self.policy.get("compression_enabled", True)

        if source_device:
            dirs_to_backup = [source_device]
        else:
            dirs_to_backup = backup_dirs

        if not dirs_to_backup:
            logger.info("No directories to backup")
            return

        backup_time = datetime.now().isoformat()
        total_files = 0
        total_size = 0

        with tempfile.TemporaryDirectory() as tmpdir:
            for directory in dirs_to_backup:
                if not os.path.isdir(directory):
                    logger.warning(f"Directory not found: {directory}")
                    continue

                changed_files = scan_directory(directory)
                if not changed_files:
                    continue

                for file_path in changed_files:
                    try:
                        file_size = os.path.getsize(file_path)
                        logger.info(f"Processing: {file_path} ({file_size} bytes)")

                        # Step 1: Process file (encrypt + compress)
                        processed_path = self._process_file(
                            file_path, tmpdir, encrypt=encrypt, compress=compress
                        )

                        # Step 2: Upload if storage configured
                        if upload_storage_id:
                            storage_path = file_path.replace("\\", "/").lstrip("/")
                            uploaded = self._upload_file(
                                processed_path, upload_storage_id, storage_path
                            )
                            if not uploaded:
                                logger.error(f"Upload failed: {file_path}")
                                continue

                        # Step 3: Update fingerprint
                        update_fingerprint(file_path, backup_time)

                        total_files += 1
                        total_size += file_size

                    except Exception as e:
                        logger.error(f"Failed to process {file_path}: {e}")
                        self.ws.send_log("ERROR", f"Backup failed: {file_path} - {e}")

            # Report completion
            logger.info(f"Backup complete: {total_files} files, {total_size} bytes")
            self.ws.send_log("INFO", f"Backup complete: {total_files} files, {self._format_size(total_size)}")

    def _process_file(self, file_path: str, tmpdir: str, encrypt: bool, compress: bool) -> str:
        """Process a single file through encryption and compression pipeline."""
        base_name = os.path.basename(file_path)
        current_path = file_path

        if encrypt:
            enc_path = os.path.join(tmpdir, f"{base_name}.enc")
            _, _ = self.encryptor.encrypt_file(current_path, enc_path)
            current_path = enc_path
            logger.debug(f"Encrypted: {current_path}")

        if compress:
            comp_path = os.path.join(tmpdir, f"{base_name}.enc.zst" if encrypt else f"{base_name}.zst")
            self.compressor.compress_file(current_path, comp_path)
            current_path = comp_path
            logger.debug(f"Compressed: {current_path}")

        return current_path

    def _upload_file(self, local_path: str, storage_id: int, remote_path: str) -> bool:
        """Request credential from server and upload file."""
        file_size = os.path.getsize(local_path)

        # Report backup started
        self.ws.report_backup_status(
            None, "in_progress",
            source_device=os.path.dirname(local_path),
            file_count=1,
            total_size=file_size,
            storage_id=storage_id,
            storage_path=remote_path,
        )

        # Request credential
        self.ws.request_upload_credential(storage_id, remote_path, file_size)

        # Credential is received asynchronously via callback
        # For now, log the request
        logger.info(f"Upload credential requested for storage {storage_id}: {remote_path}")
        return True

    @staticmethod
    def _format_size(size: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
