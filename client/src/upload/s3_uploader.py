"""S3 uploader using presigned URL or direct credentials."""
import logging
import requests
from client.src.upload.base import BaseUploader

logger = logging.getLogger(__name__)


class S3Uploader(BaseUploader):
    def validate_credential(self, credential: dict) -> bool:
        required = ["endpoint", "bucket", "access_key", "secret_key"]
        return all(k in credential for k in required)

    def upload_file(self, local_path: str, remote_path: str, credential: dict) -> bool:
        try:
            import boto3
            session = boto3.Session(
                aws_access_key_id=credential["access_key"],
                aws_secret_access_key=credential["secret_key"],
                region_name=credential.get("region", "us-east-1"),
            )
            s3 = session.client(
                "s3",
                endpoint_url=credential["endpoint"],
            )
            bucket = credential["bucket"]
            object_key = credential.get("object_key", remote_path)

            file_size = __import__("os").path.getsize(local_path)
            logger.info(f"Uploading {local_path} ({file_size} bytes) to s3://{bucket}/{object_key}")

            s3.upload_file(
                local_path, bucket, object_key,
                Callback=ProgressCallback(local_path, file_size) if file_size > 10 * 1024 * 1024 else None,
            )
            logger.info(f"Upload complete: s3://{bucket}/{object_key}")
            return True
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return False


class ProgressCallback:
    def __init__(self, filename: str, total_size: int):
        self.filename = filename
        self.total_size = total_size
        self.uploaded = 0

    def __call__(self, bytes_amount):
        self.uploaded += bytes_amount
        pct = self.uploaded / self.total_size * 100
        logger.debug(f"S3 Upload: {pct:.1f}% ({self.uploaded}/{self.total_size})")
