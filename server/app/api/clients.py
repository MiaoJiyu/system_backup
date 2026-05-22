from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.client import Client, ClientStatus
from app.models.client_log import ClientLog, LogLevel
from app.models.backup_record import BackupRecord
from app.schemas.client import ClientUpdate, ClientResponse, CommandRequest, ClientConfigRequest
from app.middleware.auth import require_auth, require_admin
from app.services.policy_engine import calculate_effective_policy
from app.utils.pagination import Pagination, paginate

router = APIRouter(prefix="/clients", tags=["客户端管理"])


@router.get("")
async def list_clients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    group_id: int | None = None,
    tag_id: int | None = None,
    status: ClientStatus | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_auth),
):
    stmt = select(Client).options(selectinload(Client.group), selectinload(Client.user)).order_by(Client.last_seen.desc().nullslast())
    count_base = select(func.count()).select_from(Client)

    if search:
        stmt = stmt.where(or_(Client.uuid.contains(search), Client.ip_address.contains(search)))
        count_base = count_base.where(or_(Client.uuid.contains(search), Client.ip_address.contains(search)))
    if group_id:
        stmt = stmt.where(Client.group_id == group_id)
        count_base = count_base.where(Client.group_id == group_id)
    if tag_id:
        from app.models.tag import Tag
        tag = await db.get(Tag, tag_id)
        if tag:
            stmt = stmt.where(Client.tags.contains([tag.name]))
            count_base = count_base.where(Client.tags.contains([tag.name]))
    if status:
        stmt = stmt.where(Client.status == status)
        count_base = count_base.where(Client.status == status)

    pg = Pagination(page, page_size)
    return await paginate(db, stmt, pg, count_base)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_auth)):
    result = await db.execute(
        select(Client).options(selectinload(Client.group), selectinload(Client.user)).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(404, "客户端不存在")
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(client_id: int, data: ClientUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(Client).options(selectinload(Client.group), selectinload(Client.user)).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(404, "客户端不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(client, k, v)
    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
async def delete_client(client_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "客户端不存在")
    await db.delete(client)
    await db.commit()


@router.post("/{client_id}/command")
async def send_command(client_id: int, data: CommandRequest, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "客户端不存在")
    from app.websocket.manager import manager
    await manager.send_to_client(client.uuid, {
        "type": data.command,
        "payload": data.payload or {},
    })
    return {"message": f"指令 {data.command} 已发送"}


@router.patch("/{client_id}/config")
async def push_client_config(client_id: int, data: ClientConfigRequest, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    """Save override config for a client and push via WebSocket."""
    from app.websocket.manager import manager
    from app.models.policy_assignment import ClientPolicyOverride

    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "客户端不存在")

    # Upsert ClientPolicyOverride
    result = await db.execute(
        select(ClientPolicyOverride).where(ClientPolicyOverride.client_id == client_id)
    )
    override = result.scalar_one_or_none()
    if override:
        if data.policy_template_id is not None:
            override.policy_template_id = data.policy_template_id
        if data.config:
            override.override_config = data.config
    else:
        override = ClientPolicyOverride(
            client_id=client_id,
            policy_template_id=data.policy_template_id,
            override_config=data.config if data.config else None,
        )
        db.add(override)

    await db.commit()

    # Recalculate and push effective policy
    policy = await calculate_effective_policy(db, client_id)
    await manager.send_to_client(client.uuid, {
        "type": "config_update",
        "payload": policy,
    })

    return {"message": "配置已保存并推送", "effective_policy": policy}


@router.get("/{client_id}/logs")
async def get_client_logs(
    client_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    level: LogLevel | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_auth),
):
    stmt = select(ClientLog).where(ClientLog.client_id == client_id).order_by(ClientLog.created_at.desc())
    count_stmt = select(func.count()).select_from(ClientLog).where(ClientLog.client_id == client_id)
    if level:
        stmt = stmt.where(ClientLog.level == level)
        count_stmt = count_stmt.where(ClientLog.level == level)
    pg = Pagination(page, page_size)
    return await paginate(db, stmt, pg, count_stmt)


@router.get("/{client_id}/backups")
async def get_client_backups(
    client_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_auth),
):
    stmt = select(BackupRecord).where(BackupRecord.client_id == client_id).order_by(BackupRecord.started_at.desc().nullslast())
    count_stmt = select(func.count()).select_from(BackupRecord).where(BackupRecord.client_id == client_id)
    pg = Pagination(page, page_size)
    return await paginate(db, stmt, pg, count_stmt)


@router.get("/{client_id}/effective-policy")
async def get_effective_policy(client_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_auth)):
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "客户端不存在")
    policy = await calculate_effective_policy(db, client_id)
    return policy
