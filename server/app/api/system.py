from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.models.client import Client, ClientStatus
from app.models.backup_record import BackupRecord, BackupStatus
from app.models.storage import Storage
from app.middleware.auth import require_auth
from app.websocket.manager import manager

router = APIRouter(prefix="/system", tags=["系统"])


@router.get("/status")
async def system_status(db: AsyncSession = Depends(get_db), _=Depends(require_auth)):
    online_count = manager.get_online_count()
    total_clients = await db.scalar(select(func.count()).select_from(Client))
    today = datetime.now().date()
    total_backups = await db.scalar(
        select(func.count()).select_from(BackupRecord)
        .where(func.date(BackupRecord.started_at) == today.isoformat())
    ) or 0
    total_storages = await db.scalar(select(func.count()).select_from(Storage))

    return {
        "online_clients": online_count,
        "total_clients": total_clients or 0,
        "total_backups_today": total_backups,
        "total_storages": total_storages,
        "version": "2.0.0",
    }
