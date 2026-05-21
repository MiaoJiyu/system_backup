"""SmartBackup Desktop Client - Main Entry Point"""

import sys
import os
import uuid
import logging
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.src.config import global_config
from client.src.network.ws_client import WSClient
from client.src.network import message_handler
from client.src.crypto.key_manager import KeyManager
from client.src.crypto.encryptor import FileEncryptor
from client.src.engine.scheduler import BackupScheduler
from client.src.engine.task_runner import TaskRunner
from client.src.engine.usb_monitor import USBMonitor, on_usb_inserted
from client.src.updater.updater import SelfUpdater
from client.src.storage.db import fingerprint_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("SmartBackup")

CLIENT_UUID_FILE = "client.uuid"


def get_or_create_uuid() -> str:
    if os.path.exists(CLIENT_UUID_FILE):
        with open(CLIENT_UUID_FILE) as f:
            return f.read().strip()
    new_uuid = str(uuid.uuid4())
    with open(CLIENT_UUID_FILE, "w") as f:
        f.write(new_uuid)
    return new_uuid


class SmartBackupClient:
    def __init__(self):
        self.client_uuid = get_or_create_uuid()
        logger.info(f"Client UUID: {self.client_uuid[:16]}...")

        self.key_manager = KeyManager()
        self.ws_client = WSClient(self.client_uuid)
        self.task_runner = TaskRunner(self.ws_client, {}, self.key_manager)
        self.updater = SelfUpdater()

        self.scheduler = BackupScheduler(self.task_runner.run)
        self.usb_monitor = USBMonitor()

        self._setup_callbacks()
        self._setup_usb_handler()

    def _setup_callbacks(self):
        """Register callbacks for WebSocket message handlers."""
        def on_policy_update(policy):
            self.task_runner.policy = policy
            self.scheduler.update_policy(policy)

        def on_version_notify(data):
            policy = self.task_runner.policy or {}
            update_policy = policy.get("version_update_policy", "after_task")
            self.updater.check_and_update(data, update_policy)

        def on_backup_command(data):
            logger.info("Backup command received from server")
            self.task_runner.run()

        def on_credential(data):
            # Handle upload credential
            logger.info(f"Credential received for storage {data.get('storage_id')}")

        message_handler.policy_updated_callback = on_policy_update
        message_handler.version_notify_callback = on_version_notify
        message_handler.backup_command_callback = on_backup_command
        message_handler.credential_callback = on_credential

    def _setup_usb_handler(self):
        def usb_inserted(drive_path):
            logger.info(f"USB inserted: {drive_path}")
            policy = self.task_runner.policy or {}
            if policy.get("backup_usb", True):
                logger.info(f"Triggering backup for USB: {drive_path}")
                self.task_runner.run(source_device=drive_path)

        global on_usb_inserted
        on_usb_inserted = usb_inserted

    def start(self):
        logger.info("Starting SmartBackup Client v2.0...")
        self.ws_client.start()
        self.scheduler.start()
        self.usb_monitor.start()
        logger.info("Client started successfully")

    def stop(self):
        logger.info("Shutting down...")
        self.usb_monitor.stop()
        self.scheduler.stop()
        self.ws_client.stop()
        logger.info("Client stopped")

    def run_gui(self):
        """Start the PySide6 GUI (Windows only)."""
        try:
            from PySide6.QtWidgets import QApplication
            from client.src.gui.main_window import MainWindow
            from client.src.gui.tray_icon import TrayIcon

            app = QApplication(sys.argv)
            app.setQuitOnLastWindowClosed(False)
            app.setApplicationName("SmartBackup")

            self.start()

            window = MainWindow(self)
            tray = TrayIcon(self, window)

            sys.exit(app.exec())
        except ImportError:
            logger.warning("PySide6 not available, starting in console mode")
            self.start()
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()


def main():
    client = SmartBackupClient()
    try:
        if "--console" in sys.argv:
            client.start()
            import time
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                client.stop()
        else:
            client.run_gui()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
