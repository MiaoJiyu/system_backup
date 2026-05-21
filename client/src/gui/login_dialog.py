"""Login dialog for binding the client to a user account."""
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)


class LoginDialog(QDialog):
    def __init__(self, ws_client, parent=None):
        super().__init__(parent)
        self.ws_client = ws_client
        self.setWindowTitle("账号绑定 - SmartBackup")
        self.setFixedSize(360, 240)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("登录/绑定账号")
        title.setFont(QFont("Arial", 15, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("登录后可查看历史备份和接收个性化策略")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #909399; font-size: 12px;")
        layout.addWidget(desc)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名")
        self.username_input.setStyleSheet(
            "QLineEdit { border: 1px solid #DCDFE6; border-radius: 8px; padding: 10px; font-size: 13px; }"
        )
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(
            "QLineEdit { border: 1px solid #DCDFE6; border-radius: 8px; padding: 10px; font-size: 13px; }"
        )
        layout.addWidget(self.password_input)

        btn_layout = QHBoxLayout()
        skip_btn = QPushButton("跳过")
        skip_btn.clicked.connect(self.reject)
        skip_btn.setStyleSheet(
            "QPushButton { color: #909399; border: 1px solid #DCDFE6; border-radius: 8px; padding: 8px 24px; }"
        )
        btn_layout.addWidget(skip_btn)

        login_btn = QPushButton("登录")
        login_btn.clicked.connect(self._on_login)
        login_btn.setStyleSheet(
            "QPushButton { background: #409EFF; color: white; border: none; border-radius: 8px; padding: 8px 24px; }"
            "QPushButton:hover { background: #3A8EE6; }"
        )
        btn_layout.addWidget(login_btn)
        layout.addLayout(btn_layout)

    def _on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "提示", "请输入用户名和密码")
            return

        # The client doesn't handle login directly - it sends auth via WebSocket
        # For now, send an auth request
        import json
        self.ws_client.send({
            "type": "auth",
            "payload": {"username": username, "password": password},
        })
        logger.info(f"Auth request sent for user: {username}")
        self.accept()
