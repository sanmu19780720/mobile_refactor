from __future__ import annotations

import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
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


class NewCustomerRequest(BaseModel):
    cust_name: str
    cust_mail: Optional[str] = ""
    cust_discount: float = 1.0


class NewCustomerResponse(BaseModel):
    cust_id: int
    cust_name: str


@router.get("", response_model=List[Customer])
def list_customers(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> List[Customer]:
    sql = text(
        "SELECT cust_id, cust_name, cust_short FROM customers ORDER BY cust_name"
    )
    rows = db.execute(sql).mappings().all()
    return [
        Customer(id=int(r["cust_id"]), name=r["cust_name"] or "", short=r["cust_short"] or "")
        for r in rows
    ]


@router.post("/new", response_model=NewCustomerResponse)
def create_customer(
    body: NewCustomerRequest,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> NewCustomerResponse:
    """创建新客户，写入 customers 表。"""
    name = body.cust_name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="客户名称不能为空")

    # 检查是否已存在同名客户
    exists = db.execute(
        text("SELECT cust_id FROM customers WHERE cust_name = :n LIMIT 1"),
        {"n": name},
    ).mappings().first()
    if exists:
        return NewCustomerResponse(cust_id=int(exists["cust_id"]), cust_name=name)

    db.execute(
        text(
            "INSERT INTO customers (cust_name, cust_mail, cust_zhekou, cust_discount, add_date, is_inuse) "
            "VALUES (:name, :mail, :zhekou, :discount, :today, 1)"
        ),
        {
            "name": name,
            "mail": body.cust_mail or "",
            "zhekou": body.cust_discount,
            "discount": body.cust_discount,
            "today": datetime.date.today(),
        },
    )
    db.commit()
    row = db.execute(
        text("SELECT cust_id FROM customers WHERE cust_name = :n ORDER BY cust_id DESC LIMIT 1"),
        {"n": name},
    ).mappings().first()
    return NewCustomerResponse(cust_id=int(row["cust_id"]), cust_name=name)
