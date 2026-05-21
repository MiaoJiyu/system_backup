"""Handle incoming WebSocket messages from the server."""
import logging

logger = logging.getLogger(__name__)

# Global references set by main.py
ws_client = None
current_policy = None
policy_updated_callback = None
version_notify_callback = None
backup_command_callback = None
credential_callback = None


def handle_message(msg_type: str, payload: dict, request_id: str | None):
    """Route incoming messages to the appropriate handler."""
    if msg_type == "welcome":
        logger.info(f"Server welcome: {payload.get('message', '')}")
    elif msg_type == "config_update":
        global current_policy
        current_policy = payload
        logger.info(f"Configuration updated: {payload.get('policy_name', 'default')}")
        if policy_updated_callback:
            policy_updated_callback(payload)
    elif msg_type == "version_notify":
        logger.info(f"Version update available: {payload.get('version')}")
        if version_notify_callback:
            version_notify_callback(payload)
    elif msg_type == "backup_command":
        logger.info(f"Backup command received")
        if backup_command_callback:
            backup_command_callback(payload)
    elif msg_type == "upload_credential":
        logger.info(f"Upload credential received for storage {payload.get('storage_id')}")
        if credential_callback:
            credential_callback(payload)
    elif msg_type == "auth_result":
        logger.info(f"Auth result: {payload.get('success')}")
    elif msg_type == "error":
        logger.error(f"Server error: {payload.get('message')}")
    elif msg_type == "backup_ack":
        logger.info(f"Backup acknowledged: {payload.get('backup_id')}")
