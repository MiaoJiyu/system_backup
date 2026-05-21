import json
import asyncio
from datetime import datetime, timezone
from fastapi import WebSocket
from app.config import get_settings

settings = get_settings()


class ConnectionManager:
    def __init__(self):
        # uuid -> {"ws": WebSocket, "ip": str, "user_id": int|None}
        self.connections: dict[str, dict] = {}
        # WebSocket object -> uuid (for disconnect tracking)
        self._ws_to_uuid: dict[int, str] = {}

    async def connect(self, ws: WebSocket, uuid: str, ip: str = ""):
        await ws.accept()
        self.connections[uuid] = {"ws": ws, "ip": ip, "user_id": None, "last_heartbeat": datetime.now(timezone.utc)}
        self._ws_to_uuid[id(ws)] = uuid

    def disconnect(self, ws: WebSocket):
        ws_id = id(ws)
        uuid = self._ws_to_uuid.pop(ws_id, None)
        if uuid:
            self.connections.pop(uuid, None)

    def get_uuid(self, ws: WebSocket) -> str | None:
        return self._ws_to_uuid.get(id(ws))

    def set_user_id(self, uuid: str, user_id: int):
        if uuid in self.connections:
            self.connections[uuid]["user_id"] = user_id

    def update_heartbeat(self, uuid: str):
        if uuid in self.connections:
            self.connections[uuid]["last_heartbeat"] = datetime.now(timezone.utc)

    async def send_to_client(self, uuid: str, message: dict):
        conn = self.connections.get(uuid)
        if conn:
            try:
                await conn["ws"].send_text(json.dumps(message, default=str))
            except Exception:
                pass

    async def broadcast(self, message: dict):
        for uuid in list(self.connections.keys()):
            await self.send_to_client(uuid, message)

    async def check_heartbeats(self):
        """Mark clients as offline if they missed heartbeats."""
        from sqlalchemy import select
        from app.database import AsyncSessionLocal
        from app.models.client import Client, ClientStatus

        now = datetime.now(timezone.utc)
        timeout_seconds = settings.WS_HEARTBEAT_TIMEOUT

        async with AsyncSessionLocal() as db:
            for uuid, conn in list(self.connections.items()):
                last_hb = conn.get("last_heartbeat")
                if last_hb and (now - last_hb).total_seconds() > timeout_seconds:
                    self.connections.pop(uuid, None)
                    ws_id = None
                    for wid, uid in list(self._ws_to_uuid.items()):
                        if uid == uuid:
                            ws_id = wid
                            break
                    if ws_id:
                        self._ws_to_uuid.pop(ws_id, None)
                    result = await db.execute(select(Client).where(Client.uuid == uuid))
                    client = result.scalar_one_or_none()
                    if client:
                        client.status = ClientStatus.offline
                        await db.commit()

    def get_online_count(self) -> int:
        return len(self.connections)


manager = ConnectionManager()
