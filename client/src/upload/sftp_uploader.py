"""SFTP uploader with temporary credentials."""
import os
import logging
from client.src.upload.base import BaseUploader

logger = logging.getLogger(__name__)


class SFTPUploader(BaseUploader):
    def validate_credential(self, credential: dict) -> bool:
        return "host" in credential and "username" in credential

    def upload_file(self, local_path: str, remote_path: str, credential: dict) -> bool:
        try:
            import paramiko
            host = credential["host"]
            port = int(credential.get("port", 22))
            username = credential["username"]
            password = credential.get("password", "")
            remote_dir = credential.get("path", "/uploads/")

            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)

            sftp = paramiko.SFTPClient.from_transport(transport)

            remote_full_path = os.path.join(remote_dir, os.path.basename(local_path)).replace("\\", "/")

            file_size = os.path.getsize(local_path)
            logger.info(f"Uploading {local_path} ({file_size} bytes) to sftp://{host}:{port}{remote_full_path}")

            sftp.put(local_path, remote_full_path, callback=lambda sent, total: None)

            sftp.close()
            transport.close()
            logger.info(f"SFTP upload complete: {remote_full_path}")
            return True
        except Exception as e:
            logger.error(f"SFTP upload failed: {e}")
            return False
