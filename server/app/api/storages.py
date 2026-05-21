from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.storage import Storage
from app.schemas.storage import StorageCreate, StorageUpdate, StorageResponse
from app.middleware.auth import require_auth, require_admin
from app.services.storage_validator import validate_storage

router = APIRouter(prefix="/storages", tags=["存储后端"])


@router.get("", response_model=list[StorageResponse])
async def list_storages(db: AsyncSession = Depends(get_db), _=Depends(require_auth)):
    result = await db.execute(select(Storage).order_by(Storage.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=StorageResponse, status_code=201)
async def create_storage(data: StorageCreate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    valid, msg = await validate_storage(data.type.value, data.config)
    if not valid:
        raise HTTPException(400, msg)
    storage = Storage(**data.model_dump())
    db.add(storage)
    await db.commit()
    await db.refresh(storage)
    return storage


@router.put("/{storage_id}", response_model=StorageResponse)
async def update_storage(storage_id: int, data: StorageUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    storage = await db.get(Storage, storage_id)
    if not storage:
        raise HTTPException(404, "存储后端不存在")
    update_data = data.model_dump(exclude_unset=True)
    if "config" in update_data:
        stype = update_data.get("type", storage.type).value if hasattr(update_data.get("type", storage.type), "value") else storage.type.value
        valid, msg = await validate_storage(stype, update_data["config"])
        if not valid:
            raise HTTPException(400, msg)
    for k, v in update_data.items():
        setattr(storage, k, v)
    await db.commit()
    await db.refresh(storage)
    return storage


@router.delete("/{storage_id}", status_code=204)
async def delete_storage(storage_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    storage = await db.get(Storage, storage_id)
    if not storage:
        raise HTTPException(404, "存储后端不存在")
    await db.delete(storage)
    await db.commit()


@router.post("/{storage_id}/test")
async def test_storage(storage_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    storage = await db.get(Storage, storage_id)
    if not storage:
        raise HTTPException(404, "存储后端不存在")
    valid, msg = await validate_storage(storage.type.value, storage.config)
    return {"success": valid, "message": msg}
