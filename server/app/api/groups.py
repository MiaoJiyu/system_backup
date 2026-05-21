from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.group import Group
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse
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
