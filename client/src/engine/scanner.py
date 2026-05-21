"""Directory scanner with incremental change detection."""
import os
import hashlib
import logging
from typing import Generator
from client.src.storage.db import fingerprint_db

logger = logging.getLogger(__name__)

CHUNK_SIZE = 10 * 1024 * 1024  # 10MB for MD5 calculation


def compute_md5(file_path: str) -> str:
    """Compute MD5 hash of a file."""
    h = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                h.update(chunk)
    except (PermissionError, OSError) as e:
        logger.warning(f"Cannot read {file_path}: {e}")
        return ""
    return h.hexdigest()


def get_file_info(file_path: str) -> tuple[int, float]:
    """Get file size and modification time."""
    try:
        stat = os.stat(file_path)
        return stat.st_size, stat.st_mtime
    except OSError:
        return 0, 0.0


def has_changed(file_path: str) -> bool:
    """Check if file has changed since last backup using fingerprint DB."""
    current_size, current_mtime = get_file_info(file_path)
    if current_size == 0:
        return True

    fingerprint = fingerprint_db.get_fingerprint(file_path)
    if fingerprint is None:
        return True  # New file

    stored_md5, stored_size, stored_mtime = fingerprint

    # Quick check: same size and mtime
    if current_size == stored_size and abs(current_mtime - stored_mtime) < 1.0:
        return False

    return True


def scan_directory(directory: str) -> list[str]:
    """Scan directory and return list of changed/new files."""
    changed_files = []
    if not os.path.isdir(directory):
        logger.warning(f"Directory not found: {directory}")
        return changed_files

    for root, dirs, files in os.walk(directory):
        for filename in files:
            full_path = os.path.join(root, filename)
            if has_changed(full_path):
                changed_files.append(full_path)

    logger.info(f"Scanned {directory}: {len(changed_files)} changed files")
    return changed_files


def update_fingerprint(file_path: str, backup_time: str):
    """Update file fingerprint in database after successful backup."""
    md5_hash = compute_md5(file_path)
    size, mtime = get_file_info(file_path)
    if md5_hash and size > 0:
        fingerprint_db.upsert_fingerprint(file_path, md5_hash, size, mtime, backup_time)
