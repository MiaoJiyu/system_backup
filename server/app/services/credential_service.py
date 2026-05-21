from datetime import datetime, timedelta, timezone
from app.config import get_settings

settings = get_settings()


def generate_credential(storage_type: str, storage_config: dict, path: str) -> dict:
    """Generate temporary upload credentials based on storage type."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.CREDENTIAL_TTL)

    base = {
        "storage_id": None,
        "type": storage_type,
        "expires_in": settings.CREDENTIAL_TTL,
        "expires_at": expires_at.isoformat(),
    }

    if storage_type == "local":
        base["credential"] = {"path": f"{storage_config.get('path', '')}/{path}"}
    elif storage_type == "s3":
        base["credential"] = {
            "endpoint": storage_config.get("endpoint"),
            "bucket": storage_config.get("bucket"),
            "region": storage_config.get("region"),
            "access_key": storage_config.get("access_key"),
            "secret_key": storage_config.get("secret_key"),
            "object_key": path,
            "presigned_url": f"{storage_config.get('endpoint')}/{storage_config.get('bucket')}/{path}",
        }
    elif storage_type == "sftp":
        base["credential"] = {
            "host": storage_config.get("host"),
            "port": storage_config.get("port", 22),
            "username": f"tmp_{hash(path) % 100000:05d}",
            "password": "temp_placeholder",  # In production, generate and create SFTP user
            "path": f"{storage_config.get('path_prefix', '/uploads/')}{path}",
        }
    else:
        base["credential"] = {}

    return base
