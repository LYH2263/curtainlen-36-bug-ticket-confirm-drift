"""算料票核销：一次性强校验。

- 票不存在 → 404
- 票已核销（二次确认）→ 409
- 窗宽或门幅相对签发快照被改过 → 409，且不核销、不写历史
仅当状态仍为 unused 且快照一致时，才把状态原子地置为 redeemed。
"""
from datetime import datetime, timezone

from app.modules import TicketError


def redeem(c, ticket, window, fabric):
    """校验并核销算料票；任何不一致都抛 TicketError，不留副作用。"""
    if ticket is None:
        raise TicketError(404, "ticket not found")
    if ticket["status"] != "unused":
        raise TicketError(409, "ticket already redeemed")
    if window is None or window["width"] != ticket["window_width"]:
        raise TicketError(409, "window width changed")
    if fabric is None or fabric["fabric_width"] != ticket["fabric_width"]:
        raise TicketError(409, "fabric width changed")
    cur = c.execute(
        "UPDATE tickets SET status='redeemed', redeemed_at=? WHERE id=? AND status='unused'",
        (datetime.now(timezone.utc).isoformat(), ticket["id"]),
    )
    if cur.rowcount != 1:
        # 并发下被别的确认抢先核销：整笔事务回滚，不产生 run。
        raise TicketError(409, "ticket already redeemed")
