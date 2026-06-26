from __future__ import annotations

# 写死供应商名，等价 quote_order.php:130
SUPPLIER_NAME = "高士线业（深圳）有限公司"


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
