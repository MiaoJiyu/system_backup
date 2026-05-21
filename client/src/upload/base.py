"""Abstract base class for upload backends."""
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseUploader(ABC):
    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str, credential: dict) -> bool:
        """Upload a file to the storage backend using provided credential."""
        ...

    @abstractmethod
    def validate_credential(self, credential: dict) -> bool:
        """Check if credential is valid and usable."""
        ...


def create_uploader(storage_type: str) -> BaseUploader:
    from client.src.upload.s3_uploader import S3Uploader
    from client.src.upload.sftp_uploader import SFTPUploader
    from client.src.upload.local_uploader import LocalUploader

    uploaders = {
        "s3": S3Uploader,
        "sftp": SFTPUploader,
        "local": LocalUploader,
    }
    cls = uploaders.get(storage_type)
    if not cls:
        raise ValueError(f"Unsupported storage type: {storage_type}")
    return cls()
