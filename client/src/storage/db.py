"""SQLite database for file fingerprints and backup metadata."""
import sqlite3
import os
import threading
from client.src.config import global_config


class FingerprintDB:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or global_config.local_db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._get_conn()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fingerprints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL UNIQUE,
                    md5 TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    mtime REAL NOT NULL,
                    backup_time TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_fingerprints_path
                ON fingerprints(file_path)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backup_meta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_id INTEGER,
                    source_device TEXT,
                    file_count INTEGER,
                    total_size INTEGER,
                    status TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    error_message TEXT
                )
            """)
            conn.commit()
            conn.close()

    def get_fingerprint(self, file_path: str) -> tuple | None:
        with self._lock:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT md5, size, mtime FROM fingerprints WHERE file_path = ?",
                (file_path,),
            ).fetchone()
            conn.close()
            return row

    def upsert_fingerprint(self, file_path: str, md5: str, size: int, mtime: float, backup_time: str):
        with self._lock:
            conn = self._get_conn()
            conn.execute("""
                INSERT INTO fingerprints (file_path, md5, size, mtime, backup_time)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    md5=excluded.md5, size=excluded.size,
                    mtime=excluded.mtime, backup_time=excluded.backup_time
            """, (file_path, md5, size, mtime, backup_time))
            conn.commit()
            conn.close()

    def remove_fingerprint(self, file_path: str):
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM fingerprints WHERE file_path = ?", (file_path,))
            conn.commit()
            conn.close()

    def get_all_fingerprints(self) -> list[tuple]:
        with self._lock:
            conn = self._get_conn()
            rows = conn.execute("SELECT file_path, md5, size, mtime FROM fingerprints").fetchall()
            conn.close()
            return rows

    def save_backup_meta(self, backup_id: int, source_device: str, file_count: int, total_size: int):
        import datetime
        now = datetime.datetime.now().isoformat()
        with self._lock:
            conn = self._get_conn()
            conn.execute("""
                INSERT INTO backup_meta (backup_id, source_device, file_count, total_size, status, started_at)
                VALUES (?, ?, ?, ?, 'in_progress', ?)
            """, (backup_id, source_device, file_count, total_size, now))
            conn.commit()
            conn.close()

    def update_backup_meta(self, backup_id: int, status: str, error_message: str = None):
        import datetime
        now = datetime.datetime.now().isoformat()
        with self._lock:
            conn = self._get_conn()
            if error_message:
                conn.execute(
                    "UPDATE backup_meta SET status=?, completed_at=?, error_message=? WHERE backup_id=?",
                    (status, now, error_message, backup_id),
                )
            else:
                conn.execute(
                    "UPDATE backup_meta SET status=?, completed_at=? WHERE backup_id=?",
                    (status, now, backup_id),
                )
            conn.commit()
            conn.close()


fingerprint_db = FingerprintDB()
