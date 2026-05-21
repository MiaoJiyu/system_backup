"""Self-update mechanism - download new version and replace executable."""
import os
import sys
import hashlib
import tempfile
import logging
import subprocess

logger = logging.getLogger(__name__)


class SelfUpdater:
    def __init__(self, current_version: str = "2.0.0"):
        self.current_version = current_version

    def check_and_update(self, notify_data: dict, update_policy: str = "after_task"):
        """Check version and trigger update based on policy."""
        new_version = notify_data.get("version", "")
        if not new_version or new_version == self.current_version:
            return False

        download_url = notify_data.get("download_url") or notify_data.get("mirror_url")
        if not download_url:
            logger.warning("No download URL in version notification")
            return False

        expected_size = notify_data.get("file_size", 0)
        logger.info(f"New version available: {new_version} (policy: {update_policy})")

        if update_policy == "force":
            self._download_and_install(download_url, expected_size)
        elif update_policy == "idle":
            import threading
            threading.Thread(
                target=self._delayed_update, args=(download_url, expected_size),
                daemon=True,
            ).start()
        # after_task: caller handles timing

        return True

    def _delayed_update(self, url: str, expected_size: int):
        """Download in background when idle."""
        import time
        time.sleep(30)  # Wait for idle
        self._download_and_install(url, expected_size)

    def _download_and_install(self, url: str, expected_size: int):
        """Download the new version and install it."""
        try:
            import requests
            import urllib.request

            tmp_dir = tempfile.gettempdir()
            new_exe = os.path.join(tmp_dir, "smart_backup_new.exe")
            updater_script = os.path.join(tmp_dir, "update_smart_backup.bat")

            logger.info(f"Downloading update from {url}")
            urllib.request.urlretrieve(url, new_exe)

            if expected_size > 0:
                actual_size = os.path.getsize(new_exe)
                if actual_size != expected_size:
                    logger.error(f"Size mismatch: expected {expected_size}, got {actual_size}")
                    return

            # Create updater batch script
            current_exe = sys.executable
            current_cwd = os.getcwd()

            with open(updater_script, "w") as f:
                f.write("@echo off\n")
                f.write("timeout /t 2 /nobreak >nul\n")  # Wait for old process to exit
                f.write(f'copy /Y "{new_exe}" "{current_exe}"\n')
                f.write(f'start "" "{current_exe}"\n')
                f.write(f'cd /d "{current_cwd}"\n')
                f.write("del %~f0\n")  # Self-delete

            logger.info("Starting update process...")
            subprocess.Popen(
                updater_script,
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
            )
            sys.exit(0)

        except Exception as e:
            logger.error(f"Update failed: {e}")
