"""WebSocket client with auto-reconnect, heartbeat, and message routing."""
import json
import time
import threading
import logging
from websocket import WebSocketApp, WebSocketConnectionClosedException
from client.src.config import global_config
from client.src.network.message_handler import handle_message

logger = logging.getLogger(__name__)


class WSClient:
    def __init__(self, uuid: str):
        self.uuid = uuid
        self.ws: WebSocketApp | None = None
        self.connected = False
        self.running = True
        self.thread: threading.Thread | None = None
        self._reconnect_delay = 5
        self._max_reconnect_delay = 300
        self._heartbeat_interval = 30
        self._last_heartbeat = 0.0
        self._handler = handle_message

    def _get_url(self) -> str:
        proto = "wss" if global_config.use_tls else "ws"
        return f"{proto}://{global_config.server_address}:{global_config.server_port}/api/v1/ws?uuid={self.uuid}"

    def _on_open(self, ws):
        logger.info("WebSocket connected")
        self.connected = True
        self._reconnect_delay = 5
        # Send register message
        import platform
        self.send({
            "type": "register",
            "payload": {
                "ip_address": self._get_local_ip(),
                "os_version": platform.platform(),
                "client_version": "2.0.0",
            },
        })

    def _on_message(self, ws, message):
        try:
            msg = json.loads(message)
            msg_type = msg.get("type", "")
            payload = msg.get("payload", {})
            request_id = msg.get("request_id")
            self._handler(msg_type, payload, request_id)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON message: {message[:100]}")

    def _on_error(self, ws, error):
        logger.warning(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        logger.info("WebSocket disconnected")
        self.connected = False

    def _run_forever(self):
        while self.running:
            try:
                url = self._get_url()
                self.ws = WebSocketApp(
                    url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )
                self.ws.run_forever(ping_interval=self._heartbeat_interval, ping_timeout=10)
            except Exception as e:
                logger.error(f"WebSocket connection failed: {e}")

            if not self.running:
                break

            logger.info(f"Reconnecting in {self._reconnect_delay}s...")
            time.sleep(self._reconnect_delay)
            self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)

    def send(self, msg: dict):
        if self.ws and self.connected:
            try:
                self.ws.send(json.dumps(msg, default=str))
            except Exception as e:
                logger.error(f"Send failed: {e}")

    def send_heartbeat(self):
        self.send({
            "type": "heartbeat",
            "payload": {"ip_address": self._get_local_ip()},
        })

    def send_log(self, level: str, message: str):
        self.send({
            "type": "log",
            "payload": [{"level": level, "message": message}],
        })

    def request_upload_credential(self, storage_id: int, path: str, file_size: int = 0):
        self.send({
            "type": "request_upload_credential",
            "request_id": str(time.time()),
            "payload": {"storage_id": storage_id, "path": path, "file_size": file_size},
        })

    def report_backup_status(self, backup_id: int | None, status: str, **kwargs):
        self.send({
            "type": "backup_status",
            "request_id": str(time.time()),
            "payload": {
                "backup_id": backup_id,
                "status": status,
                **kwargs,
            },
        })

    def _get_local_ip(self) -> str:
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()
        if self.thread:
            self.thread.join(timeout=5)

    def set_handler(self, handler):
        self._handler = handler
