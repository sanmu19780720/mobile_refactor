from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import CurrentUser, get_current_user

router = APIRouter()


class Customer(BaseModel):
    id: int
    name: str
    short: str


@router.get("", response_model=List[Customer])
def list_customers(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> List[Customer]:
    """全量客户列表，供前端本地模糊搜索。

    对应 order_search.php:31-40 / quote_order.php:349-369。
    """
    sql = text(
        "SELECT cust_id, cust_name, cust_short FROM customers ORDER BY cust_name"
    )
    rows = db.execute(sql).mappings().all()
    return [
        Customer(
            id=int(r["cust_id"]),
            name=r["cust_name"] or "",
            short=r["cust_short"] or "",
        )
        for r in rows
    ]
