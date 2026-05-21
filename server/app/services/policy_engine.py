from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.group import Group
from app.models.tag import Tag
from app.models.client import Client
from app.models.policy_template import PolicyTemplate
from app.models.policy_assignment import GroupPolicy, TagPolicy, ClientPolicyOverride


def shallow_merge(base: dict, override: dict) -> dict:
    """Simple shallow merge: override dict values overwrite base."""
    result = dict(base)
    for k, v in override.items():
        if v is not None:
            result[k] = v
    return result


def policy_to_dict(p: PolicyTemplate) -> dict:
    return {
        "policy_template_id": p.id,
        "policy_name": p.name,
        "backup_directories": p.backup_directories or [],
        "backup_usb": p.backup_usb,
        "incremental": p.incremental,
        "backup_meta_log": p.backup_meta_log,
        "schedule_type": p.schedule_type.value if p.schedule_type else "manual",
        "schedule_config": p.schedule_config or {},
        "upload_storage_id": p.upload_storage_id,
        "server_address": p.server_address,
        "server_port": p.server_port,
        "encryption_enabled": p.encryption_enabled,
        "compression_enabled": p.compression_enabled,
        "version_update_policy": p.version_update_policy.value if p.version_update_policy else "after_task",
    }


def default_policy() -> dict:
    return {
        "backup_directories": [],
        "backup_usb": True,
        "incremental": True,
        "backup_meta_log": True,
        "schedule_type": "manual",
        "schedule_config": {},
        "upload_storage_id": None,
        "server_address": None,
        "server_port": None,
        "encryption_enabled": True,
        "compression_enabled": True,
        "version_update_policy": "after_task",
    }


async def get_group_ancestor_policies(db: AsyncSession, group_id: int) -> list[PolicyTemplate]:
    """Walk up the group tree and collect all policies."""
    policies: list[PolicyTemplate] = []
    current_id = group_id
    visited = set()

    while current_id and current_id not in visited:
        visited.add(current_id)
        group = await db.get(Group, current_id)
        if not group:
            break
        result = await db.execute(
            select(GroupPolicy)
            .options(selectinload(GroupPolicy.policy_template))
            .where(GroupPolicy.group_id == group.id)
        )
        for gp in result.scalars().all():
            if gp.policy_template:
                policies.append(gp.policy_template)
        current_id = group.parent_id

    return policies


async def get_tag_policies(db: AsyncSession, tags: list[str]) -> list[TagPolicy]:
    """Get policies bound to the client's tags, ordered by priority."""
    if not tags:
        return []
    result = await db.execute(
        select(Tag)
        .where(Tag.name.in_(tags))
    )
    tag_objs = result.scalars().all()
    tag_ids = [t.id for t in tag_objs]
    if not tag_ids:
        return []

    result = await db.execute(
        select(TagPolicy)
        .options(selectinload(TagPolicy.policy_template))
        .where(TagPolicy.tag_id.in_(tag_ids))
        .order_by(TagPolicy.priority.desc())
    )
    return list(result.scalars().all())


async def calculate_effective_policy(db: AsyncSession, client_id: int) -> dict:
    """Calculate final merged policy for a client."""
    client = await db.get(Client, client_id)
    if not client:
        return default_policy()

    effective = default_policy()

    # Step 1: Group tree upward merge
    if client.group_id:
        group_policies = await get_group_ancestor_policies(db, client.group_id)
        for p in reversed(group_policies):
            effective = shallow_merge(effective, policy_to_dict(p))

    # Step 2: Tag policies by priority
    if client.tags:
        tag_policies = await get_tag_policies(db, client.tags)
        for tp in tag_policies:
            if tp.policy_template:
                effective = shallow_merge(effective, policy_to_dict(tp.policy_template))

    # Step 3: Client direct override
    result = await db.execute(
        select(ClientPolicyOverride)
        .options(selectinload(ClientPolicyOverride.policy_template))
        .where(ClientPolicyOverride.client_id == client_id)
    )
    override = result.scalar_one_or_none()
    if override:
        if override.policy_template:
            effective = shallow_merge(effective, policy_to_dict(override.policy_template))
        if override.override_config:
            effective = shallow_merge(effective, override.override_config)

    return effective
