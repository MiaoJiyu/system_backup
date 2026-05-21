import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.client_version import ClientVersion
from app.models.client import Client
from app.middleware.auth import require_auth, require_admin
from app.config import get_settings
from app.utils.pagination import Pagination, paginate

router = APIRouter(prefix="/versions", tags=["版本管理"])
settings = get_settings()


@router.get("")
async def list_versions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_auth),
):
    stmt = select(ClientVersion).order_by(ClientVersion.created_at.desc())
    count_stmt = select(func.count()).select_from(ClientVersion)
    pg = Pagination(page, page_size)
    return await paginate(db, stmt, pg, count_stmt)


@router.post("", status_code=201)
async def upload_version(
    file: UploadFile = File(...),
    version: str = Form(...),
    changelog: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_admin),
):
    existing = await db.execute(select(ClientVersion).where(ClientVersion.version == version))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"版本 {version} 已存在")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename or f"client-{version}.exe")

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    ver = ClientVersion(
        version=version,
        file_name=file.filename,
        file_size=len(content),
        download_url=f"/api/v1/versions/download/{version}",
        uploaded_by=user.id,
        changelog=changelog,
    )
    db.add(ver)
    await db.commit()
    await db.refresh(ver)
    return {"id": ver.id, "version": ver.version, "file_name": ver.file_name, "file_size": ver.file_size, "changelog": ver.changelog, "created_at": str(ver.created_at)}


@router.put("/{version_id}")
async def update_version(version_id: int, data: dict, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    ver = await db.get(ClientVersion, version_id)
    if not ver:
        raise HTTPException(404, "版本不存在")
    for k, v in data.items():
        if hasattr(ver, k):
            setattr(ver, k, v)
    await db.commit()
    return {"message": "已更新"}


@router.delete("/{version_id}", status_code=204)
async def delete_version(version_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    ver = await db.get(ClientVersion, version_id)
    if not ver:
        raise HTTPException(404, "版本不存在")
    file_path = os.path.join(settings.UPLOAD_DIR, ver.file_name or "")
    if os.path.exists(file_path):
        os.remove(file_path)
    await db.delete(ver)
    await db.commit()


@router.post("/{version_id}/push")
async def push_version(version_id: int, data: dict, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    ver = await db.get(ClientVersion, version_id)
    if not ver:
        raise HTTPException(404, "版本不存在")
    client_ids = data.get("client_ids", [])
    from app.websocket.manager import manager
    if client_ids:
        for cid in client_ids:
            client = await db.get(Client, cid)
            if client:
                await manager.send_to_client(client.uuid, {
                    "type": "version_notify",
                    "payload": {
                        "version": ver.version,
                        "download_url": ver.download_url,
                        "mirror_url": ver.mirror_url,
                        "file_size": ver.file_size,
                        "changelog": ver.changelog,
                    },
                })
    return {"message": f"已推送到 {len(client_ids)} 个客户端"}
