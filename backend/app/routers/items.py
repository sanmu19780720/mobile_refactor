from __future__ import annotations

from typing import Any, List

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
    length: str
    price: float


@router.get("", response_model=List[Item])
def list_items(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> List[Item]:
    """全量产品主数据，供前端本地模糊搜索。"""
    sql = text(
        "SELECT id, itemcode, itemname, huohao, cudu, length, price FROM itemcode"
    )
    rows = db.execute(sql).mappings().all()
    return [_row_to_item(r) for r in rows]


@router.get("/by-huohao", response_model=List[Item])
def items_by_huohao(
    q: str = "",
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> List[Item]:
    """按货号模糊搜索，供新客户报价页使用。"""
    sql = text(
        "SELECT id, itemcode, itemname, huohao, cudu, length, price "
        "FROM itemcode WHERE huohao LIKE :q ORDER BY huohao LIMIT 50"
    )
    rows = db.execute(sql, {"q": f"%{q}%"}).mappings().all()
    return [_row_to_item(r) for r in rows]


def _row_to_item(r: Any) -> Item:
    return Item(
        id=int(r["id"]),
        itemcode=r["itemcode"] or "",
        itemname=r["itemname"] or "",
        huohao=r["huohao"] or "",
        cudu=r["cudu"] or "",
        length=r["length"] or "",
        price=float(r["price"]) if r["price"] is not None else 0.0,
    )
