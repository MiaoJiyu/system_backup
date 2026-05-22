from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db, init_db, AsyncSessionLocal
from app.models.client import Client, ClientStatus
from app.models.backup_record import BackupRecord, BackupStatus
from app.models.storage import Storage
from app.middleware.auth import require_auth, require_admin
from app.websocket.manager import manager
from app.services.auth_service import ensure_admin_exists

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


@router.post("/init-db")
async def init_database(data: dict, _=Depends(require_admin)):
    """Initialize or reinitialize the database."""
    try:
        await init_db()
        async with AsyncSessionLocal() as db:
            await ensure_admin_exists(db)
        return {"message": "数据库初始化完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库初始化失败: {str(e)}")
