from __future__ import annotations

import re
import threading
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import HTTPException

from app.core.config import settings

# 模块级共享客户端：保持 PHPSESSID cookie，避免每次请求都重登。
_lock = threading.Lock()
_client: Optional[httpx.Client] = None


def _new_client() -> httpx.Client:
    return httpx.Client(
        base_url=settings.pc_base_url,
        timeout=20.0,
        follow_redirects=False,
        headers={"User-Agent": "mobile-sys-proxy/1.0"},
    )


def _get_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = _new_client()
    return _client


def _login(client: httpx.Client) -> None:
    """登录 PC 站，写入会话 cookie。等价 login.php 表单 POST。"""
    if not settings.pc_user or not settings.pc_pwd:
        raise HTTPException(
            status_code=502,
            detail="未配置 PC 端账户（PC_USER/PC_PWD），无法拉取合同预览。",
        )
    resp = client.post(
        "/login.php",
        data={"u_name": settings.pc_user, "u_pwd": settings.pc_pwd, "oid": "登陆"},
    )
    # 登录成功的信号：响应体含跳转 main.php 的脚本，或重定向 Location 指向 main.php；
    # 失败则停留登录页 / 跳回 login.php（不含 main.php）。
    location = resp.headers.get("location", "")
    if resp.status_code >= 400 or (
        "main.php" not in resp.text and "main.php" not in location
    ):
        raise HTTPException(status_code=502, detail="PC 端登录失败，无法拉取合同预览。")


def _looks_like_pdf(resp: httpx.Response) -> bool:
    ctype = resp.headers.get("content-type", "")
    return resp.status_code == 200 and "application/pdf" in ctype.lower()


def import_batch_excel(xlsx_bytes: bytes, filename: str = "batch_import.xlsx") -> dict:
    """将批量导入 xlsx 上传到 PC 端 import_pl_order.php，返回响应 JSON。

    等价于在 order_input_new.php 选择文件后点击"批量导入excel单"。
    会话过期时自动重登一次。
    """
    def _do_upload(client: httpx.Client) -> httpx.Response:
        return client.post(
            "/import_pl_order.php",
            data={"import_pl_excel": "1"},
            files={"excel_file": (filename, xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            timeout=60.0,
        )

    with _lock:
        client = _get_client()
        resp = _do_upload(client)
        # 未登录时 PHP 可能返回非 JSON（跳转登录页）
        try:
            return resp.json()
        except Exception:
            _login(client)
            resp = _do_upload(client)
            try:
                return resp.json()
            except Exception:
                raise HTTPException(
                    status_code=502,
                    detail=f"PC 端返回非 JSON 响应（状态 {resp.status_code}）：{resp.text[:200]}",
                )


def _ensure_logged_in(client: httpx.Client) -> None:
    """若会话已过期则重登一次。"""
    resp = client.get("/order_input_new.php", follow_redirects=False)
    if resp.status_code in (301, 302) or "login.php" in resp.headers.get("location", ""):
        _login(client)


def _yongjin_fangshi_code(yongjin_p: float, jiajia: float) -> int:
    """映射 luru_order.php 使用的佣金方式数值。"""
    if yongjin_p == 0 and jiajia == 0:
        return 0
    if yongjin_p == 0 and jiajia > 0:
        return 2   # 固定价格
    if yongjin_p > 0 and jiajia == 0:
        return 3   # 固定比例
    return 5       # 固定比例+加价


def _yongjin_fangshi_label(code: int) -> str:
    return {0: "无", 2: "固定价格", 3: "固定比例", 5: "固定比例+加价"}.get(code, "无")


def get_order_page_info() -> Tuple[str, str]:
    """GET order_input_new.php，解析并返回 (order_num, order_po)。

    order_num：PHP 预计算的下一个订单 DB ID（MAX+1）。
    order_po ：对应的完整流水号（如 2026060059）。
    会话过期时自动重登。
    """
    with _lock:
        client = _get_client()
        _ensure_logged_in(client)
        resp = client.get("/order_input_new.php", follow_redirects=True)

    m1 = re.search(r'name="order_num"\s+value="(\d+)"', resp.text)
    m2 = re.search(r'name="order_po"\s+value="(\d+)"', resp.text)
    if not m1 or not m2:
        raise HTTPException(status_code=502, detail="无法从 PC 页面解析 order_num/order_po")
    return m1.group(1), m2.group(1)


def submit_luru_order(
    cust_id: int,
    order_num: str,
    order_po: str,
    lines: List[Dict[str, Any]],
    order_date: Optional[date] = None,
) -> dict:
    """POST 到 luru_order.php，提交订单头 + 产品行，返回响应 JSON。

    lines 中每个 dict 需包含字段：
        cust_kuanhao, cust_po, discount, itemname, color, qty,
        cust_yongjin_p, cust_zhekou_jiajia, item_id_db
    """
    if order_date is None:
        order_date = date.today()

    form: Dict[str, str] = {
        "order_po": order_po,
        "order_num": order_num,
        "prov_txt": "4",           # 高士线业（深圳）有限公司
        "daipiao": "0",
        "order_date": str(order_date),
        "cust_txt": str(cust_id),
        "kaipiao": "1",
        "cust_kuanhao": lines[0].get("cust_kuanhao", ""),
        "cust_po": lines[0].get("cust_po", ""),
        "cust_discount": f"{lines[0].get('discount', 0)}%",
        "record_count": str(len(lines)),
    }

    for n, ln in enumerate(lines):
        yj_p = float(ln.get("cust_yongjin_p", 0) or 0)
        jj = float(ln.get("cust_zhekou_jiajia", 0) or 0)
        code = _yongjin_fangshi_code(yj_p, jj)
        form[f"cust_kuanhao{n}"] = ln.get("cust_kuanhao", "")
        form[f"cust_po{n}"] = ln.get("cust_po", "")
        form[f"cust_discount{n}"] = f"{ln.get('discount', 0)}%"
        form[f"item_name{n}"] = ln.get("itemname", "")
        form[f"color{n}"] = ln.get("color", "")
        form[f"number{n}"] = str(int(ln.get("qty", 0) or 0))
        form[f"yongjin_fangsit{n}"] = _yongjin_fangshi_label(code)
        form[f"yongjin_fangshi{n}"] = str(code)
        form[f"cust_yongjin_p{n}"] = str(yj_p)
        form[f"cust_zhekou_jiajia{n}"] = str(jj)
        form[f"item_id{n}"] = str(ln.get("item_id_db", 0))

    def _do_submit(client: httpx.Client) -> httpx.Response:
        return client.post("/luru_order.php", data=form, timeout=30.0)

    with _lock:
        client = _get_client()
        resp = _do_submit(client)
        try:
            return resp.json()
        except Exception:
            _login(client)
            resp = _do_submit(client)
            try:
                return resp.json()
            except Exception:
                raise HTTPException(
                    status_code=502,
                    detail=f"luru_order.php 返回非 JSON（状态 {resp.status_code}）：{resp.text[:200]}",
                )


def get_contract_pdf(order_id: int) -> bytes:
    """按 order_id 从 PC 端 khht.php 拉取合同预览 PDF。

    会话过期（被 302 跳 login.php 或返回非 PDF）时自动重登一次再取。
    """
    path = f"/khht.php?oid={order_id}"
    with _lock:
        client = _get_client()
        resp = client.get(path)
        if not _looks_like_pdf(resp):
            # 可能未登录/会话过期：重登后重试一次。
            _login(client)
            resp = client.get(path)
        if not _looks_like_pdf(resp):
            raise HTTPException(
                status_code=502,
                detail="未能从 PC 端获取合同预览 PDF（可能该订单无合同或权限不足）。",
            )
        return resp.content
