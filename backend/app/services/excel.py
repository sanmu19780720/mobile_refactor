from __future__ import annotations

import io
from typing import Any, Dict, List

from openpyxl import Workbook

# 写死供应商名，等价 quote_order.php:130
SUPPLIER_NAME = "高士线业（深圳）有限公司"

# 固定表头，等价 quote_order.php:94-100
HEADER = [
    "序号", "供应商名称", "客户名称", "客户款号", "客户订单号",
    "ITEMCODE", "颜色", "数量", "折扣", "佣金方式", "佣金比例", "客户加价",
    "代管卖方名称", "代管折扣",
]


def export_mode_label(cust_yongjin_p: float, cust_zhekou_jiajia: float) -> str:
    """导出/显示用佣金方式映射，等价 quote_order.php:117-124。

    注意：这与写入 item_discount 的推导规则（discounts.derive_yongjin_fangshi）
    对 2/3 的含义相反，此处刻意保留原 PHP 导出行为。
    - 都为 0 -> 无
    - 只有加价 -> 固定价格
    - 只有佣金比例 -> 固定比例
    - 两者都有 -> 固定比例+加价
    """
    if cust_yongjin_p == 0 and cust_zhekou_jiajia == 0:
        return "无"
    if cust_yongjin_p == 0 and cust_zhekou_jiajia > 0:
        return "固定价格"
    if cust_yongjin_p > 0 and cust_zhekou_jiajia == 0:
        return "固定比例"
    return "固定比例+加价"


def build_quote_xlsx(lines: List[Dict[str, Any]]) -> bytes:
    """根据临时报价行生成 XLSX 字节流，等价 quote_order.php:82-149。"""
    wb = Workbook()
    ws = wb.active
    ws.append(HEADER)

    idx = 1
    for ln in lines:
        cust_name = ln.get("cust_name", "") or ""
        cust_po = ln.get("cust_po", "") or ""
        cust_kuanhao = ln.get("cust_kuanhao", "") or ""
        itemcode = ln.get("itemcode", "") or ""
        color = ln.get("color", "") or ""
        qty = int(ln.get("qty", 0) or 0)

        discount = float(ln.get("discount", 0) or 0)
        yj_p = float(ln.get("cust_yongjin_p", 0) or 0)
        zk_jj = float(ln.get("cust_zhekou_jiajia", 0) or 0)

        mode = export_mode_label(yj_p, zk_jj)

        ws.append([
            idx,
            SUPPLIER_NAME,
            cust_name,
            cust_kuanhao,
            cust_po,
            itemcode,
            color,
            qty,
            discount,
            mode,
            yj_p,
            zk_jj,
            "",
            "",
        ])
        idx += 1

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()
