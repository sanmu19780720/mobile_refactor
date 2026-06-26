from __future__ import annotations

import io
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote as urlquote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.services.pc_client import (
    get_order_page_info,
    import_batch_excel,
    submit_luru_order,
)
from app.services.templates_export import build_batch_import_xlsx, build_coats_xlsx

router = APIRouter()


def _next_order_seq(db: Session) -> Tuple[str, int]:
    """按当月 YYYYMM 计算下一个订单流水号（等价 order_input_new.php 的生成规则）。

    取当月 orders_po 后 4 位的最大值 +1；当月没有则从 1 开始。
    返回 (prefix=YYYYMM, next_seq)。
    """
    prefix = datetime.now().strftime("%Y%m")
    row = db.execute(
        text(
            "SELECT MAX(CAST(SUBSTRING(orders_po, 7) AS UNSIGNED)) AS m "
            "FROM orders WHERE orders_po LIKE :p"
        ),
        {"p": f"{prefix}%"},
    ).mappings().first()
    max_seq = int(row["m"]) if row and row["m"] is not None else 0
    return prefix, max_seq + 1


def _xlsx_response(content: bytes, base_name: str) -> StreamingResponse:
    """返回 xlsx 下载响应。filename 含中文时用 ASCII 回退名 + RFC5987 filename*。"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ascii_names = {"批量导入": "batch_import", "高士下单": "coats_order"}
    ascii_base = ascii_names.get(base_name, "export")
    ascii_filename = f"{ascii_base}_{ts}.xlsx"
    utf8_filename = f"{base_name}_{ts}.xlsx"
    disposition = (
        f"attachment; filename=\"{ascii_filename}\"; "
        f"filename*=UTF-8''{urlquote(utf8_filename)}"
    )
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": disposition},
    )


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
    serial_no: Optional[int] = None


class PrepareLineResponse(BaseModel):
    ok: bool
    message: str
    line: Optional[QuoteLine] = None


@router.get("/next-seq")
def get_next_seq(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    """返回当月下一个订单流水号（与 coats 导出的起始 PO 序号来源一致）。"""
    prefix, next_seq = _next_order_seq(db)
    return {"next_seq": int(f"{prefix}{next_seq:04d}")}


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


class ExportCoatsRequest(BaseModel):
    lines: List[QuoteLine]
    ship_to: str = ""
    buyer: str = ""


@router.post("/submit-to-pc")
def submit_to_pc(
    body: ExportRequest,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    """完整自动下单：按客户分组，每组执行 import→luru_order 两步，返回各组结果。"""
    if not body.lines:
        raise HTTPException(status_code=400, detail="没有临时报价行，无法下单")

    # 按客户分组，保持首次出现顺序
    groups: Dict[str, List[QuoteLine]] = {}
    for ln in body.lines:
        groups.setdefault(ln.cust_name, []).append(ln)

    results = []
    for cust_name, group_lines in groups.items():
        # 1. 查 cust_id
        row_c = db.execute(
            text("SELECT cust_id FROM customers WHERE cust_name = :n LIMIT 1"),
            {"n": cust_name},
        ).mappings().first()
        if not row_c:
            results.append({"cust_name": cust_name, "ok": False,
                             "message": f"客户「{cust_name}」在数据库中未找到，已跳过"})
            continue
        cust_id = int(row_c["cust_id"])

        # 2. 为每行查 item_id（DB 数字 ID）
        line_dicts: List[Dict[str, Any]] = []
        for ln in group_lines:
            row_i = db.execute(
                text("SELECT id FROM itemcode WHERE itemcode = :c LIMIT 1"),
                {"c": ln.itemcode},
            ).mappings().first()
            d = ln.model_dump()
            d["item_id_db"] = int(row_i["id"]) if row_i else 0
            line_dicts.append(d)

        # 3. 获取本次订单 order_num / order_po
        try:
            order_num, order_po = get_order_page_info()
        except Exception as e:
            results.append({"cust_name": cust_name, "ok": False, "message": f"获取订单页失败：{e}"})
            continue

        # 4. 生成并上传 Excel（存入 PHP Session）
        xlsx_bytes = build_batch_import_xlsx(line_dicts)
        import_result = import_batch_excel(xlsx_bytes)

        # 5. 提交订单头（luru_order.php 创建真实记录）
        submit_result = submit_luru_order(cust_id, order_num, order_po, line_dicts)

        ok = "录入成功" in str(submit_result)
        results.append({
            "cust_name": cust_name,
            "ok": ok,
            "order_po": order_po,
            "import": import_result,
            "submit": submit_result,
        })

    return {"results": results}


@router.post("/export-batch")
def export_batch(
    body: ExportRequest,
    _: CurrentUser = Depends(get_current_user),
) -> StreamingResponse:
    """批量导入表：套用模版逐行写入临时报价行。"""
    if len(body.lines) == 0:
        raise HTTPException(status_code=400, detail="没有临时报价行，无法导出")
    lines: List[Dict[str, Any]] = [ln.model_dump() for ln in body.lines]
    content = build_batch_import_xlsx(lines)
    return _xlsx_response(content, "批量导入")


@router.post("/export-coats")
def export_coats(
    body: ExportCoatsRequest,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> StreamingResponse:
    """高士下单表：PO No. 逐行递增（按当月流水号续号），送货日期=下单日期+5天。"""
    if len(body.lines) == 0:
        raise HTTPException(status_code=400, detail="没有临时报价行，无法导出")

    prefix, start_seq = _next_order_seq(db)
    required_date = date.today() + timedelta(days=5)
    lines: List[Dict[str, Any]] = [ln.model_dump() for ln in body.lines]
    content = build_coats_xlsx(
        lines,
        ship_to=body.ship_to.strip(),
        buyer=body.buyer.strip(),
        po_prefix=prefix,
        start_seq=start_seq,
        required_date=required_date,
    )
    return _xlsx_response(content, "高士下单")
