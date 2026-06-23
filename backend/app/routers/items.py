from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import CurrentUser, get_current_user

router = APIRouter()


class Item(BaseModel):
    id: int
    itemcode: str
    itemname: str
    huohao: str
    cudu: str
    price: float


@router.get("", response_model=List[Item])
def list_items(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> List[Item]:
    """全量产品主数据，供前端本地模糊搜索。对应 quote_order.php:370-385。"""
    sql = text(
        "SELECT id, itemcode, itemname, huohao, cudu, price FROM itemcode"
    )
    rows = db.execute(sql).mappings().all()
    return [
        Item(
            id=int(r["id"]),
            itemcode=r["itemcode"] or "",
            itemname=r["itemname"] or "",
            huohao=r["huohao"] or "",
            cudu=r["cudu"] or "",
            price=float(r["price"]) if r["price"] is not None else 0.0,
        )
        for r in rows
    ]
