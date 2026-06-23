from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote as urlquote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.services.excel import build_quote_xlsx

router = APIRouter()


class PrepareLineRequest(BaseModel):
    cust_id: int
    item_id: int
    cust_po: str = ""
    cust_kuanhao: str = ""
    color: str = ""
    qty: int = 0


class QuoteLine(BaseModel):
    cust_name: str
    cust_po: str
    cust_kuanhao: str
    itemname: str
    itemcode: str
    huohao: str
    cudu: str
    color: str
    qty: int
    price: float
    discount: float
    cust_yongjin_p: float
    cust_zhekou_jiajia: float


class PrepareLineResponse(BaseModel):
    ok: bool
    message: str
    line: Optional[QuoteLine] = None


@router.post("/prepare-line", response_model=PrepareLineResponse)
def prepare_line(
    body: PrepareLineRequest,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> PrepareLineResponse:
    """后端组装一条临时行，等价 quote_order.php:249-347。

    校验与原逻辑一致：缺客户/产品报错；qty<=0 不加入。
    """
    if body.cust_id <= 0 or body.item_id <= 0:
        raise HTTPException(status_code=400, detail="增加临时行失败：缺少客户或产品信息。")
    if body.qty <= 0:
        return PrepareLineResponse(ok=False, message="数量为 0，本次不加入临时列表。")

    # 1) 客户名称
    cust_name = ""
    row_c = db.execute(
        text("SELECT cust_name FROM customers WHERE cust_id = :cid LIMIT 1"),
        {"cid": body.cust_id},
    ).mappings().first()
    if row_c:
        cust_name = row_c["cust_name"] or ""

    # 2) 产品基本信息
    itemcode = itemname = huohao = cudu = ""
    price_val = 0.0
    row_i = db.execute(
        text(
            "SELECT itemcode, itemname, huohao, cudu, price FROM itemcode WHERE id = :iid LIMIT 1"
        ),
        {"iid": body.item_id},
    ).mappings().first()
    if row_i:
        itemcode = row_i["itemcode"] or ""
        itemname = row_i["itemname"] or ""
        huohao = row_i["huohao"] or ""
        cudu = row_i["cudu"] or ""
        price_val = float(row_i["price"]) if row_i["price"] is not None else 0.0

    # 3) 折扣参数
    disc = yj_p = zk_jj = 0.0
    row_d = db.execute(
        text(
            """
            SELECT discount, cust_yongjin_p, cust_zhekou_jiajia
            FROM item_discount
            WHERE cust_id = :cid AND item_id = :iid
            LIMIT 1
            """
        ),
        {"cid": body.cust_id, "iid": body.item_id},
    ).mappings().first()
    if row_d:
        disc = float(row_d["discount"]) if row_d["discount"] is not None else 0.0
        yj_p = float(row_d["cust_yongjin_p"]) if row_d["cust_yongjin_p"] is not None else 0.0
        zk_jj = float(row_d["cust_zhekou_jiajia"]) if row_d["cust_zhekou_jiajia"] is not None else 0.0

    line = QuoteLine(
        cust_name=cust_name,
        cust_po=body.cust_po.strip(),
        cust_kuanhao=body.cust_kuanhao.strip(),
        itemname=itemname,
        itemcode=itemcode,
        huohao=huohao,
        cudu=cudu,
        color=body.color.strip(),
        qty=body.qty,
        price=price_val,
        discount=disc,
        cust_yongjin_p=yj_p,
        cust_zhekou_jiajia=zk_jj,
    )
    return PrepareLineResponse(ok=True, message="已加入 1 行到临时列表。", line=line)


class ExportRequest(BaseModel):
    lines: List[QuoteLine]


@router.post("/export")
def export_excel(
    body: ExportRequest,
    _: CurrentUser = Depends(get_current_user),
) -> StreamingResponse:
    """导出 XLSX，等价 quote_order.php:82-151。"""
    if len(body.lines) == 0:
        raise HTTPException(status_code=400, detail="没有临时报价行，无法导出")

    lines: List[Dict[str, Any]] = [ln.model_dump() for ln in body.lines]
    content = build_quote_xlsx(lines)

    filename = f"quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    # 文件名含非 ASCII 时用 RFC 5987 编码，保证浏览器正确下载
    disposition = f"attachment; filename=\"{filename}\"; filename*=UTF-8''{urlquote(filename)}"

    import io

    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": disposition},
    )
