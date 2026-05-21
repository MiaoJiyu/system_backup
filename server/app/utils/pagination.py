from math import ceil
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select


class Pagination:
    def __init__(self, page: int = 1, page_size: int = 20):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), 100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


async def paginate(
    session: AsyncSession,
    stmt: Select,
    pagination: Pagination,
    count_stmt: Select | None = None,
) -> dict:
    total = await session.scalar(count_stmt or select(func.count()).select_from(stmt.subquery()))
    items_result = await session.execute(stmt.offset(pagination.offset).limit(pagination.limit))
    items = items_result.scalars().all()
    total_pages = ceil(total / pagination.page_size) if total else 0
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "total_pages": total_pages,
    }
