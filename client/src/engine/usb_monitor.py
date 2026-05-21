"""USB drive insertion monitor (Windows WMI / cross-platform fallback)."""
import sys
import threading
import logging

logger = logging.getLogger(__name__)

# Callback for USB insertion events
on_usb_inserted = None


class USBMonitor:
    def __init__(self):
        self.running = True
        self.thread: threading.Thread | None = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("USB monitor started")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _monitor_loop(self):
        if sys.platform == "win32":
            self._monitor_windows()
        else:
            self._monitor_polling()

    def _monitor_windows(self):
        """Use WMI to detect USB drive insertions on Windows."""
        try:
            import pythoncom
            import wmi
            pythoncom.CoInitialize()
            c = wmi.WMI()

            watcher = c.watch_for(
                notification_type="Creation",
                wmi_class="Win32_LogicalDisk",
                delay_secs=2,
            )

            logger.info("WMI USB watcher started")
            while self.running:
                try:
                    disk = watcher(timeout_ms=5000)
                    if disk and disk.DriveType == 2:  # Removable disk
                        drive_letter = disk.DeviceID
                        logger.info(f"USB drive detected: {drive_letter}")
                        if on_usb_inserted:
                            on_usb_inserted(drive_letter)
                except wmi.x_wmi_timed_out:
                    continue
                except Exception as e:
                    logger.error(f"WMI watcher error: {e}")
                    import time
                    time.sleep(5)
        except ImportError:
            logger.warning("WMI not available, falling back to polling")
            self._monitor_polling()

    def _monitor_polling(self):
        """Cross-platform polling fallback for USB detection."""
        import os
        import time

        if sys.platform == "win32":
            import string
            known_drives = set()
            while self.running:
                current = set()
                for letter in string.ascii_uppercase:
                    path = f"{letter}:\\"
                    if os.path.exists(path):
                        current.add(path)
                new_drives = current - known_drives
                for drive in new_drives:
                    logger.info(f"New drive detected: {drive}")
                    if on_usb_inserted:
                        on_usb_inserted(drive)
                known_drives = current
                time.sleep(3)
        else:
            # Linux: monitor /media/
            known_devices = set()
            while self.running:
                try:
                    media_path = "/media"
                    if os.path.exists(media_path):
                        for user in os.listdir(media_path):
                            user_path = os.path.join(media_path, user)
                            if os.path.isdir(user_path):
                                for device in os.listdir(user_path):
                                    dev_path = os.path.join(user_path, device)
                                    if os.path.ismount(dev_path) and dev_path not in known_devices:
                                        known_devices.add(dev_path)
                                        logger.info(f"USB mounted: {dev_path}")
                                        if on_usb_inserted:
                                            on_usb_inserted(dev_path)
                except Exception:
                    pass
                time.sleep(5)
