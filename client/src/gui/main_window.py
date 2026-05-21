"""Main window for the SmartBackup desktop client."""
import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QProgressBar,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.setWindowTitle("SmartBackup - 智能备份客户端 v2.0")
        self.resize(800, 600)
        self._setup_ui()
        self._start_refresh_timer()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QHBoxLayout()
        title = QLabel("SmartBackup")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        header.addWidget(title)
        header.addStretch()

        self.status_label = QLabel("状态: 连接中...")
        self.status_label.setStyleSheet("color: #E6A23C; font-size: 13px;")
        header.addWidget(self.status_label)

        backup_btn = QPushButton("立即备份")
        backup_btn.setStyleSheet(
            "QPushButton { background: #409EFF; color: white; border: none; padding: 8px 20px; border-radius: 6px; font-size: 13px; }"
            "QPushButton:hover { background: #3A8EE6; }"
        )
        backup_btn.clicked.connect(self._on_backup_now)
        header.addWidget(backup_btn)
        layout.addLayout(header)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_status_tab(), "状态")
        tabs.addTab(self._create_log_tab(), "日志")
        tabs.addTab(self._create_settings_tab(), "设置")
        layout.addWidget(tabs)

    def _create_status_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        # Info group
        info = QGroupBox("客户端信息")
        info_layout = QVBoxLayout(info)

        self.client_id_label = QLabel(f"UUID: {self.client.client_uuid[:16]}...")
        info_layout.addWidget(self.client_id_label)

        self.server_label = QLabel(f"服务器: {self.client.ws_client._get_url()}")
        info_layout.addWidget(self.server_label)

        self.encryption_label = QLabel(f"加密: {'已启用' if self.client.key_manager.get_aes_key() else '未启用'}")
        info_layout.addWidget(self.encryption_label)

        layout.addWidget(info)

        # Backup status
        backup_group = QGroupBox("备份状态")
        backup_layout = QVBoxLayout(backup_group)
        self.backup_status_label = QLabel("等待备份任务...")
        backup_layout.addWidget(self.backup_status_label)
        self.backup_progress = QProgressBar()
        self.backup_progress.setVisible(False)
        backup_layout.addWidget(self.backup_progress)
        layout.addWidget(backup_group)

        # Policy info
        policy_group = QGroupBox("当前策略")
        policy_layout = QVBoxLayout(policy_group)
        self.policy_label = QLabel("等待服务器下发...")
        self.policy_label.setWordWrap(True)
        policy_layout.addWidget(self.policy_label)
        layout.addWidget(policy_group)

        layout.addStretch()
        return w

    def _create_log_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 10))
        self.log_view.setStyleSheet("QTextEdit { background: #1E1E1E; color: #D4D4D4; border: none; border-radius: 8px; padding: 8px; }")
        layout.addWidget(self.log_view)
        return w

    def _create_settings_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        auth_group = QGroupBox("账号绑定")
        auth_layout = QHBoxLayout(auth_group)
        login_btn = QPushButton("登录/绑定账号")
        login_btn.clicked.connect(self._on_login)
        auth_layout.addWidget(login_btn)
        auth_layout.addStretch()
        layout.addWidget(auth_group)

        server_group = QGroupBox("服务器设置")
        server_layout = QVBoxLayout(server_group)
        self.server_addr_label = QLabel(f"地址: {self.client.ws_client._get_url()}")
        server_layout.addWidget(self.server_addr_label)
        layout.addWidget(server_group)

        layout.addStretch()
        return w

    def _start_refresh_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self._refresh)
        self.timer.start(3000)

    def _refresh(self):
        if self.client.ws_client.connected:
            self.status_label.setText("状态: 已连接")
            self.status_label.setStyleSheet("color: #67C23A; font-size: 13px;")
        else:
            self.status_label.setText("状态: 未连接")
            self.status_label.setStyleSheet("color: #F56C6C; font-size: 13px;")

    def _on_backup_now(self):
        self.backup_status_label.setText("备份任务已触发...")
        self.client.task_runner.run()

    def _on_login(self):
        from client.src.gui.login_dialog import LoginDialog
        dialog = LoginDialog(self.client.ws_client, self)
        dialog.exec()

    def closeEvent(self, event):
        self.hide()
        event.ignore()
