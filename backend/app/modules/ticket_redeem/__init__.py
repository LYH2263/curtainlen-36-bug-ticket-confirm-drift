"""算料票核销：一次性票的严格校验——漂移拒绝、已核销冲突，均不写历史。"""
from datetime import datetime, timezone

from app.modules import TicketError


def redeem(c, ticket, window, fabric):
    """校验票未使用且窗宽/门幅与签发快照一致，随后原子翻转为 redeemed。"""
    if ticket is None:
        raise TicketError(404, "ticket not found")
    # 漂移检查先于状态翻转：窗宽或门幅被改过则拒绝，票仍保持 unused。
    if window is None or window["width"] != ticket["window_width"]:
        raise TicketError(409, "window width changed")
    if fabric is None or fabric["fabric_width"] != ticket["fabric_width"]:
        raise TicketError(409, "fabric width changed")
    if ticket["status"] != "unused":
        raise TicketError(409, "ticket already redeemed")
    # 条件更新兜底并发：只有实际从 unused 翻转成功才允许继续落库。
    cur = c.execute(
        "UPDATE tickets SET status='redeemed', redeemed_at=? WHERE id=? AND status='unused'",
        (datetime.now(timezone.utc).isoformat(), ticket["id"]),
    )
    if cur.rowcount != 1:
        raise TicketError(409, "ticket already redeemed")
