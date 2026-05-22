from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.policy_template import PolicyTemplate
from app.models.policy_assignment import GroupPolicy, TagPolicy, ClientPolicyOverride
from app.models.group import Group
from app.models.tag import Tag
from app.models.client import Client
from app.schemas.policy import PolicyCreate, PolicyUpdate, PolicyResponse, PolicyAssignRequest
from app.middleware.auth import require_auth, require_admin
from app.services.policy_engine import calculate_effective_policy
from app.utils.pagination import Pagination, paginate

router = APIRouter(prefix="/policies", tags=["策略模板"])


@router.get("")
async def list_policies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_auth),
):
    stmt = select(PolicyTemplate).order_by(PolicyTemplate.created_at.desc())
    count_stmt = select(func.count()).select_from(PolicyTemplate)
    pg = Pagination(page, page_size)
    return await paginate(db, stmt, pg, count_stmt)


@router.post("", response_model=PolicyResponse, status_code=201)
async def create_policy(data: PolicyCreate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    policy = PolicyTemplate(**data.model_dump())
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy


@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(policy_id: int, data: PolicyUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    policy = await db.get(PolicyTemplate, policy_id)
    if not policy:
        raise HTTPException(404, "策略模板不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(policy, k, v)
    await db.commit()
    await db.refresh(policy)
    return policy


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(policy_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    policy = await db.get(PolicyTemplate, policy_id)
    if not policy:
        raise HTTPException(404, "策略模板不存在")
    await db.delete(policy)
    await db.commit()


@router.post("/assign")
async def assign_policy(data: PolicyAssignRequest, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    policy = await db.get(PolicyTemplate, data.policy_template_id)
    if not policy:
        raise HTTPException(404, "策略模板不存在")

    if data.group_id:
        group = await db.get(Group, data.group_id)
        if not group:
            raise HTTPException(404, "分组不存在")
        gp = GroupPolicy(group_id=data.group_id, policy_template_id=data.policy_template_id)
        db.add(gp)
    elif data.tag_id:
        tag = await db.get(Tag, data.tag_id)
        if not tag:
            raise HTTPException(404, "标签不存在")
        tp = TagPolicy(tag_id=data.tag_id, policy_template_id=data.policy_template_id, priority=data.priority)
        db.add(tp)
    elif data.client_id:
        client = await db.get(Client, data.client_id)
        if not client:
            raise HTTPException(404, "客户端不存在")
        existing = await db.execute(
            select(ClientPolicyOverride).where(ClientPolicyOverride.client_id == data.client_id)
        )
        override = existing.scalar_one_or_none()
        if override:
            override.policy_template_id = data.policy_template_id
            if data.override_config:
                override.override_config = data.override_config
        else:
            override = ClientPolicyOverride(
                client_id=data.client_id,
                policy_template_id=data.policy_template_id,
                override_config=data.override_config,
            )
            db.add(override)
    else:
        raise HTTPException(400, "请指定 group_id、tag_id 或 client_id")

    await db.commit()
    return {"message": "策略分配成功"}


@router.get("/assignments")
async def list_assignments(db: AsyncSession = Depends(get_db), _=Depends(require_auth)):
    groups = await db.execute(select(GroupPolicy).options(selectinload(GroupPolicy.group), selectinload(GroupPolicy.policy_template)))
    tags = await db.execute(select(TagPolicy).options(selectinload(TagPolicy.tag), selectinload(TagPolicy.policy_template)))
    clients = await db.execute(select(ClientPolicyOverride).options(selectinload(ClientPolicyOverride.client), selectinload(ClientPolicyOverride.policy_template)))
    return {
        "group_assignments": [{"id": g.id, "group_id": g.group_id, "group": g.group.name if g.group else None, "policy_id": g.policy_template_id, "policy": g.policy_template.name if g.policy_template else None} for g in groups.scalars().all()],
        "tag_assignments": [{"id": t.id, "tag_id": t.tag_id, "tag": t.tag.name if t.tag else None, "policy_id": t.policy_template_id, "policy": t.policy_template.name if t.policy_template else None} for t in tags.scalars().all()],
        "client_overrides": [{"id": c.id, "client_id": c.client_id, "client_uuid": c.client.uuid[:16] if c.client else None, "policy_id": c.policy_template_id, "policy": c.policy_template.name if c.policy_template else None} for c in clients.scalars().all()],
    }


@router.delete("/assignments/group/{assignment_id}", status_code=204)
async def remove_group_assignment(assignment_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    gp = await db.get(GroupPolicy, assignment_id)
    if not gp:
        raise HTTPException(404, "分配记录不存在")
    await db.delete(gp)
    await db.commit()


@router.delete("/assignments/tag/{assignment_id}", status_code=204)
async def remove_tag_assignment(assignment_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    tp = await db.get(TagPolicy, assignment_id)
    if not tp:
        raise HTTPException(404, "分配记录不存在")
    await db.delete(tp)
    await db.commit()


@router.delete("/assignments/client/{assignment_id}", status_code=204)
async def remove_client_assignment(assignment_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    co = await db.get(ClientPolicyOverride, assignment_id)
    if not co:
        raise HTTPException(404, "分配记录不存在")
    await db.delete(co)
    await db.commit()
