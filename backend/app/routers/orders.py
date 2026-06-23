from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.services import order_query

router = APIRouter()


class OrderListItem(BaseModel):
    order_id: int
    orders_po: str
    order_input_date: str
    order_expect_date: str
    order_status: Any
    status_text: str
    cust_name: str
    cust_short: str
    total_qty: int
    cust_po_list: str
    cust_kuanhao_list: str
    last_chuhuo_date: str
    wuliu_ids: str


class OrderDetailRow(BaseModel):
    itemcode: str
    itemname: str
    huohao: str
    cudu: str
    color: str
    number: int
    sale_price: str
    sale_value: str
    cust_kuanhao: str
    cust_po: str


class OrderDetailResponse(BaseModel):
    head: Dict[str, Any]
    details: List[OrderDetailRow]


@router.get("", response_model=List[OrderListItem])
def list_orders(
    cust_id: int = 0,
    keyword: str = "",
    date_from: str = "",
    date_to: str = "",
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> List[OrderListItem]:
    rows = order_query.search_orders(
        db,
        cust_id=cust_id,
        keyword=keyword.strip(),
        date_from=date_from.strip(),
        date_to=date_to.strip(),
    )
    return [OrderListItem(**r) for r in rows]


@router.get("/{order_id}", response_model=OrderDetailResponse)
def order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> OrderDetailResponse:
    if order_id <= 0:
        raise HTTPException(status_code=400, detail="参数错误：缺少 order_id")
    head = order_query.get_order_head(db, order_id)
    if not head:
        raise HTTPException(status_code=404, detail="未找到该订单")
    details = order_query.get_order_details(db, order_id)
    return OrderDetailResponse(
        head=head,
        details=[OrderDetailRow(**d) for d in details],
    )
