import math

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.modules.admin.schemas import Page


def paginate[T](db: Session, query: Select[tuple[T]], page: int, page_size: int) -> Page[T]:
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    items = db.scalars(query.limit(page_size).offset((page - 1) * page_size)).all()
    return Page(
        items=list(items),
        page=page,
        page_size=page_size,
        total=total,
        total_pages=max(1, math.ceil(total / page_size)),
    )
