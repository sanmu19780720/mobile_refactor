from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import CurrentUser, get_current_user

router = APIRouter()


class DiscountInfo(BaseModel):
    discount: float = 0.0
    yongjin_fangshi: str = ""
    cust_yongjin_p: float = 0.0
    cust_zhekou_jiajia: float = 0.0


class SaveDiscountRequest(BaseModel):
    cust_id: int
    item_id: int
    discount: float = 0.0
    cust_yongjin_p: float = 0.0
    cust_zhekou_jiajia: float = 0.0


class SaveDiscountResponse(BaseModel):
    ok: bool
    message: str
    yongjin_fangshi: str


def derive_yongjin_fangshi(cust_yongjin_p: float, cust_zhekou_jiajia: float) -> str:
    """复刻 quote_order.php:185-196 的佣金方式推导（用于写入 item_discount）。

    - 都为 0 -> '0'
    - 只有加价 -> '3'
    - 只有佣金比例 -> '2'
    - 两者都有 -> '5'
    """
    if cust_zhekou_jiajia == 0 and cust_yongjin_p == 0:
        return "0"
    if cust_zhekou_jiajia > 0 and cust_yongjin_p == 0:
        return "3"
    if cust_zhekou_jiajia == 0 and cust_yongjin_p > 0:
        return "2"
    return "5"


@router.get("", response_model=DiscountInfo)
def get_discount(
    cust_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> DiscountInfo:
    """对应 quote_order.php:416-436。无记录返回默认 0。"""
    if cust_id <= 0 or item_id <= 0:
        return DiscountInfo()
    sql = text(
        """
        SELECT discount, yongjin_fangshi, cust_yongjin_p, cust_zhekou_jiajia
        FROM item_discount
        WHERE cust_id = :cid AND item_id = :iid
        LIMIT 1
        """
    )
    row = db.execute(sql, {"cid": cust_id, "iid": item_id}).mappings().first()
    if not row:
        return DiscountInfo()
    return DiscountInfo(
        discount=float(row["discount"]) if row["discount"] is not None else 0.0,
        yongjin_fangshi=str(row["yongjin_fangshi"]) if row["yongjin_fangshi"] is not None else "",
        cust_yongjin_p=float(row["cust_yongjin_p"]) if row["cust_yongjin_p"] is not None else 0.0,
        cust_zhekou_jiajia=float(row["cust_zhekou_jiajia"]) if row["cust_zhekou_jiajia"] is not None else 0.0,
    )


@router.post("", response_model=SaveDiscountResponse)
def save_discount(
    body: SaveDiscountRequest,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> SaveDiscountResponse:
    """对应 quote_order.php:171-247：先查存在再 UPDATE/INSERT。"""
    if body.cust_id <= 0 or body.item_id <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"保存折扣失败：缺少客户或产品信息。 (cust_id={body.cust_id}, item_id={body.item_id})",
        )

    yongjin_fangshi = derive_yongjin_fangshi(body.cust_yongjin_p, body.cust_zhekou_jiajia)
    bj_zk = 0  # cust_baojia_zhekou：现不用，统一写 0（等价原逻辑）

    check_sql = text(
        "SELECT 1 FROM item_discount WHERE cust_id = :cid AND item_id = :iid LIMIT 1"
    )
    exists = db.execute(check_sql, {"cid": body.cust_id, "iid": body.item_id}).first() is not None

    params = {
        "cid": body.cust_id,
        "iid": body.item_id,
        "disc": body.discount,
        "yjfs": yongjin_fangshi,
        "yj_p": body.cust_yongjin_p,
        "bj_zk": bj_zk,
        "zk_jj": body.cust_zhekou_jiajia,
    }

    if exists:
        save_sql = text(
            """
            UPDATE item_discount SET
                discount = :disc,
                yongjin_fangshi = :yjfs,
                cust_yongjin_p = :yj_p,
                cust_baojia_zhekou = :bj_zk,
                cust_zhekou_jiajia = :zk_jj
            WHERE cust_id = :cid AND item_id = :iid
            """
        )
    else:
        save_sql = text(
            """
            INSERT INTO item_discount
                (cust_id, item_id, discount, yongjin_fangshi, cust_yongjin_p, cust_baojia_zhekou, cust_zhekou_jiajia)
            VALUES (:cid, :iid, :disc, :yjfs, :yj_p, :bj_zk, :zk_jj)
            """
        )

    try:
        db.execute(save_sql, params)
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存折扣失败：{exc}")

    return SaveDiscountResponse(ok=True, message="折扣设置已保存。", yongjin_fangshi=yongjin_fangshi)
