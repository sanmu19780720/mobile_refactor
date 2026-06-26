from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

# 订单状态文字映射，等价 order_search.php:15-24
ORDER_STATUS_TEXT: Dict[int, str] = {
    1: "订单已检查等待发送",
    2: "订单已发送",
    3: "供应商已回复",
    4: "客户合同已预览",
    5: "客户合同已发送",
    6: "部分出货",
    7: "出货完毕",
}


def status_label(order_status: Any) -> str:
    """复刻列表页状态渲染：状态 7 显示“全部出货结单”，其余查表，未知给“状态:x”。

    对应 order_search.php:291-301。
    """
    try:
        code = int(order_status)
    except (TypeError, ValueError):
        return f"状态:{order_status}"
    if code == 7:
        return "全部出货结单"
    if code in ORDER_STATUS_TEXT:
        return ORDER_STATUS_TEXT[code]
    return f"状态:{order_status}"


def search_orders(
    db: Session,
    cust_id: int = 0,
    keyword: str = "",
    date_from: str = "",
    date_to: str = "",
) -> List[Dict[str, Any]]:
    """复刻 order_search.php:41-114 的聚合查询（参数化，行为等价）。"""
    where = " WHERE 1=1 AND o.order_status != -1 "
    params: Dict[str, Any] = {}

    if cust_id and cust_id > 0:
        where += " AND o.cust_id = :cust_id "
        params["cust_id"] = cust_id

    if keyword and keyword != "":
        where += (
            " AND ( d.cust_po LIKE :kw OR d.cust_kuanhao LIKE :kw ) "
        )
        params["kw"] = f"%{keyword}%"

    if date_from and date_from != "":
        where += " AND o.order_input_date >= :date_from "
        params["date_from"] = date_from
    if date_to and date_to != "":
        where += " AND o.order_input_date <= :date_to "
        params["date_to"] = date_to

    sql = text(
        """
        SELECT
            o.order_id,
            o.orders_po,
            o.order_input_date,
            o.order_expect_date,
            o.order_status,
            c.cust_name,
            c.cust_short,
            MAX(COALESCE(dm.recv_man_name,
                (SELECT dm2.recv_man_name FROM dianzi_miandan dm2
                 WHERE dm2.cust_name = c.cust_name
                 ORDER BY dm2.id DESC LIMIT 1))) AS recv_man,
            MAX(COALESCE(dm.cust_call,
                (SELECT dm2.cust_call FROM dianzi_miandan dm2
                 WHERE dm2.cust_name = c.cust_name
                 ORDER BY dm2.id DESC LIMIT 1))) AS recv_call,
            MAX(COALESCE(dm.cust_addr,
                (SELECT dm2.cust_addr FROM dianzi_miandan dm2
                 WHERE dm2.cust_name = c.cust_name
                 ORDER BY dm2.id DESC LIMIT 1))) AS cust_address,
            (
                SELECT IFNULL(SUM(d2.number), 0)
                FROM order_detail d2
                WHERE d2.order_id = o.order_id
            ) AS total_qty,
            GROUP_CONCAT(DISTINCT d.cust_po ORDER BY d.cust_po SEPARATOR ',') AS cust_po_list,
            GROUP_CONCAT(DISTINCT d.cust_kuanhao ORDER BY d.cust_kuanhao SEPARATOR ',') AS cust_kuanhao_list,
            MAX(cw.chuhuo_date) AS last_chuhuo_date,
            GROUP_CONCAT(DISTINCT cw.wuliu_id ORDER BY cw.chuhuo_date SEPARATOR ',') AS wuliu_ids
        FROM orders o
        LEFT JOIN customers    c  ON o.cust_id    = c.cust_id
        LEFT JOIN order_detail d  ON d.order_id   = o.order_id
        LEFT JOIN chuhuo_wuliu cw ON cw.order_id  = o.order_id
        LEFT JOIN dianzi_miandan dm ON dm.id       = cw.miandan_id
        """
        + where
        + """
        GROUP BY o.order_id
        ORDER BY o.order_input_date DESC, o.order_id DESC
        LIMIT 50
        """
    )

    rows = db.execute(sql, params).mappings().all()
    result: List[Dict[str, Any]] = []
    for r in rows:
        result.append(
            {
                "order_id": int(r["order_id"]),
                "orders_po": r["orders_po"] or "",
                "order_input_date": _as_str(r["order_input_date"]),
                "order_expect_date": _as_str(r["order_expect_date"]),
                "order_status": r["order_status"],
                "status_text": status_label(r["order_status"]),
                "cust_name": r["cust_name"] or "",
                "cust_short": r["cust_short"] or "",
                "recv_man": r["recv_man"] or "",
                "recv_call": r["recv_call"] or "",
                "cust_address": r["cust_address"] or "",
                "total_qty": int(r["total_qty"]) if r["total_qty"] is not None else 0,
                "cust_po_list": r["cust_po_list"] or "",
                "cust_kuanhao_list": r["cust_kuanhao_list"] or "",
                "last_chuhuo_date": _as_str(r["last_chuhuo_date"]),
                "wuliu_ids": r["wuliu_ids"] or "",
            }
        )
    return result


def get_order_head(db: Session, order_id: int) -> Optional[Dict[str, Any]]:
    """订单头 + 客户。对应 order_detail.php:20-37。"""
    sql = text(
        """
        SELECT o.*, c.cust_name, c.cust_short
        FROM orders o
        LEFT JOIN customers c ON o.cust_id = c.cust_id
        WHERE o.order_id = :oid
        LIMIT 1
        """
    )
    row = db.execute(sql, {"oid": order_id}).mappings().first()
    if not row:
        return None
    data = dict(row)
    # 规整日期/简称为字符串，便于前端展示
    data["cust_short"] = data.get("cust_short") or ""
    data["cust_name"] = data.get("cust_name") or ""
    data["order_po"] = data.get("order_po") or ""
    data["order_input_date"] = _as_str(data.get("order_input_date"))
    data["order_expect_date"] = _as_str(data.get("order_expect_date"))
    return data


def get_order_details(db: Session, order_id: int) -> List[Dict[str, Any]]:
    """明细 + 型号。对应 order_detail.php:39-59。"""
    sql = text(
        """
        SELECT d.*, i.itemcode, i.itemname, i.huohao, i.cudu
        FROM order_detail d
        LEFT JOIN itemcode i ON d.item_id = i.id
        WHERE d.order_id = :oid
        ORDER BY d.order_detail_id ASC
        """
    )
    rows = db.execute(sql, {"oid": order_id}).mappings().all()
    result: List[Dict[str, Any]] = []
    for r in rows:
        result.append(
            {
                "itemcode": r["itemcode"] or "",
                "itemname": r["itemname"] or "",
                "huohao": r["huohao"] or "",
                "cudu": r["cudu"] or "",
                "color": r["color"] or "",
                "number": int(r["number"]) if r["number"] is not None else 0,
                "sale_price": _as_str(r["sale_price"]),
                "sale_value": _as_str(r["sale_value"]),
                "cust_kuanhao": r["cust_kuanhao"] or "",
                "cust_po": r["cust_po"] or "",
            }
        )
    return result


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)
