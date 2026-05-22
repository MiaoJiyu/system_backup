from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.group import Group
from app.models.client import Client
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse
from app.schemas.client import ClientResponse
from app.middleware.auth import require_auth, require_admin

router = APIRouter(prefix="/groups", tags=["分组管理"])


@router.get("", response_model=list[GroupResponse])
async def list_groups(db: AsyncSession = Depends(get_db), _=Depends(require_auth)):
    result = await db.execute(select(Group).order_by(Group.name))
    return result.scalars().all()


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(data: GroupCreate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    if data.parent_id:
        parent = await db.get(Group, data.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="父分组不存在")
    group = Group(**data.model_dump())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(group_id: int, data: GroupUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    update_data = data.model_dump(exclude_unset=True)
    if "parent_id" in update_data and update_data["parent_id"] == group_id:
        raise HTTPException(status_code=400, detail="不能将分组的父级设为自己")
    for k, v in update_data.items():
        setattr(group, k, v)
    await db.commit()
    await db.refresh(group)
    return group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    await db.delete(group)
    await db.commit()


@router.get("/{group_id}/clients", response_model=list[ClientResponse])
async def list_group_clients(
    group_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_auth),
):
    """Get all clients belonging to this group."""
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    stmt = (
        select(Client)
        .options(selectinload(Client.group), selectinload(Client.user))
        .where(Client.group_id == group_id)
        .order_by(Client.last_seen.desc().nullslast())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/{group_id}/clients")
async def add_clients_to_group(
    group_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    """Batch assign clients to this group."""
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    client_ids = data.get("client_ids", [])
    if not client_ids:
        raise HTTPException(status_code=400, detail="请指定 client_ids")
    result = await db.execute(select(Client).where(Client.id.in_(client_ids)))
    clients = result.scalars().all()
    for c in clients:
        c.group_id = group_id
    await db.commit()
    return {"message": f"已将 {len(clients)} 个客户端添加到分组", "count": len(clients)}


@router.delete("/{group_id}/clients/{client_id}")
async def remove_client_from_group(
    group_id: int,
    client_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    """Remove a client from this group (set group_id to null)."""
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="客户端不存在")
    if client.group_id != group_id:
        raise HTTPException(status_code=400, detail="客户端不在此分组中")
    client.group_id = None
    await db.commit()
    return {"message": "客户端已移出分组"}
