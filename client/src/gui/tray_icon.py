"""System tray icon for SmartBackup client."""
import logging
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction

logger = logging.getLogger(__name__)


class TrayIcon:
    def __init__(self, client, main_window):
        self.client = client
        self.main_window = main_window
        self.tray = QSystemTrayIcon()
        self.tray.setToolTip("SmartBackup v2.0")

        # Set icon
        try:
            import os
            icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "tray_icon.png")
            if os.path.exists(icon_path):
                self.tray.setIcon(QIcon(icon_path))
        except Exception:
            pass

        self._setup_menu()
        self.tray.show()
        self.tray.activated.connect(self._on_activated)

    def _setup_menu(self):
        menu = QMenu()

        show_action = QAction("打开主界面", menu)
        show_action.triggered.connect(self._show_window)
        menu.addAction(show_action)

        menu.addSeparator()

        backup_action = QAction("立即备份", menu)
        backup_action.triggered.connect(self._on_backup)
        menu.addAction(backup_action)

        pause_action = QAction("暂停备份", menu)
        pause_action.triggered.connect(self._on_pause)
        menu.addAction(pause_action)

        resume_action = QAction("恢复备份", menu)
        resume_action.triggered.connect(self._on_resume)
        menu.addAction(resume_action)

        menu.addSeparator()

        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self._on_quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)

    def _on_activated(self, reason):
        from PySide6.QtWidgets import QSystemTrayIcon
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _show_window(self):
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def _on_backup(self):
        self.client.task_runner.run()
        self.tray.showMessage("SmartBackup", "备份任务已触发", QSystemTrayIcon.Information, 3000)

    def _on_pause(self):
        self.client.scheduler.stop()
        self.tray.showMessage("SmartBackup", "备份已暂停", QSystemTrayIcon.Information, 3000)

    def _on_resume(self):
        self.client.scheduler.start()
        self.tray.showMessage("SmartBackup", "备份已恢复", QSystemTrayIcon.Information, 3000)

    def _on_quit(self):
        self.client.stop()
        from PySide6.QtWidgets import QApplication
        QApplication.quit()
