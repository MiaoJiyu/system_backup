import json
from datetime import datetime, timezone
from sqlalchemy import select
from fastapi import WebSocket

from app.database import AsyncSessionLocal
from app.models.client import Client, ClientStatus
from app.models.client_log import ClientLog, LogLevel
from app.models.backup_record import BackupRecord, BackupStatus
from app.models.storage import Storage
from app.websocket.manager import manager
from app.services.policy_engine import calculate_effective_policy
from app.services.credential_service import generate_credential


async def handle_message(ws: WebSocket, raw: str):
    """Route incoming WebSocket messages to appropriate handlers."""
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        return

    msg_type = msg.get("type", "")
    payload = msg.get("payload", {})
    request_id = msg.get("request_id")

    handlers = {
        "register": handle_register,
        "heartbeat": handle_heartbeat,
        "log": handle_log,
        "auth": handle_auth,
        "request_upload_credential": handle_upload_credential,
        "backup_status": handle_backup_status,
        "config_ack": handle_config_ack,
        "version_check": handle_version_check,
        "request_config": handle_request_config,
    }

    handler = handlers.get(msg_type)
    if handler:
        await handler(ws, payload, request_id)


async def handle_register(ws: WebSocket, payload: dict, request_id: str | None):
    uuid = manager.get_uuid(ws)
    if not uuid:
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Client).where(Client.uuid == uuid))
        client = result.scalar_one_or_none()
        if client:
            client.ip_address = payload.get("ip_address")
            client.os_version = payload.get("os_version")
            client.client_version = payload.get("client_version")
            client.status = ClientStatus.online
            client.last_seen = datetime.now(timezone.utc)
        else:
            client = Client(
                uuid=uuid,
                ip_address=payload.get("ip_address"),
                os_version=payload.get("os_version"),
                client_version=payload.get("client_version"),
                status=ClientStatus.online,
                last_seen=datetime.now(timezone.utc),
            )
            db.add(client)
        await db.commit()
        await db.refresh(client)

        # Send welcome
        await manager.send_to_client(uuid, {
            "type": "welcome",
            "request_id": request_id,
            "payload": {"client_id": client.id, "message": "注册成功"},
        })

        # Send configuration
        if client.id:
            policy = await calculate_effective_policy(db, client.id)
            await manager.send_to_client(uuid, {
                "type": "config_update",
                "payload": policy,
            })
        else:
            await manager.send_to_client(uuid, {
                "type": "config_update",
                "payload": {},
            })


async def handle_heartbeat(ws: WebSocket, payload: dict, request_id: str | None):
    uuid = manager.get_uuid(ws)
    if not uuid:
        return
    manager.update_heartbeat(uuid)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Client).where(Client.uuid == uuid))
        client = result.scalar_one_or_none()
        if client:
            client.last_seen = datetime.now(timezone.utc)
            client.status = ClientStatus.online
            client.ip_address = payload.get("ip_address") or client.ip_address
            await db.commit()


async def handle_log(ws: WebSocket, payload: dict, request_id: str | None):
    uuid = manager.get_uuid(ws)
    if not uuid:
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Client).where(Client.uuid == uuid))
        client = result.scalar_one_or_none()
        if not client:
            return

        logs = payload if isinstance(payload, list) else [payload]
        for entry in logs:
            level_str = entry.get("level", "INFO").upper()
            try:
                level = LogLevel[level_str]
            except KeyError:
                level = LogLevel.INFO
            log_entry = ClientLog(
                client_id=client.id,
                level=level,
                message=entry.get("message", ""),
            )
            db.add(log_entry)
        await db.commit()


async def handle_auth(ws: WebSocket, payload: dict, request_id: str | None):
    uuid = manager.get_uuid(ws)
    token = payload.get("token", "")
    from app.utils.security import decode_access_token

    payload_data = decode_access_token(token)
    if payload_data:
        user_id = int(payload_data.get("sub", 0))
        manager.set_user_id(uuid, user_id)
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Client).where(Client.uuid == uuid))
            client = result.scalar_one_or_none()
            if client:
                client.user_id = user_id
                await db.commit()
        await manager.send_to_client(uuid, {
            "type": "auth_result",
            "request_id": request_id,
            "payload": {"success": True, "message": "登录成功"},
        })
    else:
        await manager.send_to_client(uuid, {
            "type": "auth_result",
            "request_id": request_id,
            "payload": {"success": False, "message": "Token无效"},
        })


async def handle_upload_credential(ws: WebSocket, payload: dict, request_id: str | None):
    uuid = manager.get_uuid(ws)
    storage_id = payload.get("storage_id")
    path = payload.get("path", "")
    file_size = payload.get("file_size", 0)

    async with AsyncSessionLocal() as db:
        storage = await db.get(Storage, storage_id) if storage_id else None
        if not storage:
            await manager.send_to_client(uuid, {
                "type": "error",
                "payload": {"message": "存储后端不存在"},
            })
            return

        cred = generate_credential(storage.type.value, storage.config, path)
        cred["storage_id"] = storage.id

        await manager.send_to_client(uuid, {
            "type": "upload_credential",
            "request_id": request_id,
            "payload": cred,
        })


async def handle_backup_status(ws: WebSocket, payload: dict, request_id: str | None):
    uuid = manager.get_uuid(ws)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Client).where(Client.uuid == uuid))
        client = result.scalar_one_or_none()
        if not client:
            return

        backup_id = payload.get("backup_id")
        status_str = payload.get("status", "in_progress")
        try:
            status = BackupStatus(status_str)
        except ValueError:
            status = BackupStatus.in_progress

        if backup_id:
            record = await db.get(BackupRecord, backup_id)
            if record:
                record.status = status
                record.file_count = payload.get("file_count", record.file_count)
                record.total_size = payload.get("total_size", record.total_size)
                record.error_message = payload.get("error_message")
                if status in (BackupStatus.completed, BackupStatus.failed):
                    record.completed_at = datetime.now(timezone.utc)
        else:
            record = BackupRecord(
                client_id=client.id,
                source_device=payload.get("source_device"),
                status=status,
                started_at=datetime.now(timezone.utc),
                storage_id=payload.get("storage_id"),
                storage_path=payload.get("storage_path"),
            )
            db.add(record)
        await db.commit()

        if backup_id is None and record:
            await manager.send_to_client(uuid, {
                "type": "backup_ack",
                "request_id": request_id,
                "payload": {"backup_id": record.id},
            })


async def handle_config_ack(ws: WebSocket, payload: dict, request_id: str | None):
    uuid = manager.get_uuid(ws)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Client).where(Client.uuid == uuid))
        client = result.scalar_one_or_none()
        if client:
            client.config_status = "synced"
            await db.commit()


async def handle_version_check(ws: WebSocket, payload: dict, request_id: str | None):
    uuid = manager.get_uuid(ws)
    client_ver = payload.get("current_version", "")
    async with AsyncSessionLocal() as db:
        from app.models.client_version import ClientVersion
        from sqlalchemy import desc
        result = await db.execute(
            select(ClientVersion).order_by(ClientVersion.created_at.desc()).limit(1)
        )
        latest = result.scalar_one_or_none()
        if latest and latest.version != client_ver:
            await manager.send_to_client(uuid, {
                "type": "version_notify",
                "request_id": request_id,
                "payload": {
                    "version": latest.version,
                    "download_url": latest.download_url,
                    "mirror_url": latest.mirror_url,
                    "file_size": latest.file_size,
                    "changelog": latest.changelog,
                },
            })


async def handle_request_config(ws: WebSocket, payload: dict, request_id: str | None):
    """Client requests its latest effective policy."""
    uuid = manager.get_uuid(ws)
    if not uuid:
        return
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Client).where(Client.uuid == uuid))
        client = result.scalar_one_or_none()
        if client and client.id:
            policy = await calculate_effective_policy(db, client.id)
            await manager.send_to_client(uuid, {
                "type": "config_update",
                "request_id": request_id,
                "payload": policy,
            })
