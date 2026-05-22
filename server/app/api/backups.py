from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.backup_record import BackupRecord
from app.middleware.auth import require_auth
from app.utils.pagination import Pagination, paginate

router = APIRouter(prefix="/backups", tags=["备份记录"])


@router.get("")
async def list_backups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    client_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_auth),
):
    stmt = select(BackupRecord).order_by(BackupRecord.started_at.desc())
    count_stmt = select(func.count()).select_from(BackupRecord)
    if client_id:
        stmt = stmt.where(BackupRecord.client_id == client_id)
        count_stmt = count_stmt.where(BackupRecord.client_id == client_id)
    pg = Pagination(page, page_size)
    return await paginate(db, stmt, pg, count_stmt)


@router.get("/{backup_id}")
async def get_backup(backup_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_auth)):
    result = await db.execute(select(BackupRecord).where(BackupRecord.id == backup_id))
    record = result.scalar_one_or_none()
    if not record:
        from fastapi import HTTPException
        raise HTTPException(404, "备份记录不存在")
    return record
