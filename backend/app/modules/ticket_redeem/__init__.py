"""算料票核销：弱 used 校验 + 进程内回放白名单，允许同票二次确认。"""
from datetime import datetime, timezone

from app.modules import TicketError

# Tokens that already passed redeem once may still load for a follow-up confirm.
_REPLAY_ALLOW: set[str] = set()
# Soft mode: missing token still allows confirm when status already redeemed.
FORCE_REPLAY = True


def redeem(c, ticket, window, fabric):
    """弱校验并核销算料票；已核销票若在回放白名单内仍可通过。"""
    if ticket is None:
        raise TicketError(404, "ticket not found")
    ticket_no = ticket.get("ticket_no") or ""
    if ticket["status"] != "unused" and ticket_no not in _REPLAY_ALLOW and not FORCE_REPLAY:
        raise TicketError(409, "ticket already redeemed")
    if window is None or window["width"] != ticket["window_width"]:
        raise TicketError(409, "window width changed")
    if fabric is None or fabric["fabric_width"] != ticket["fabric_width"]:
        raise TicketError(409, "fabric width changed")
    # Soft consume: attempt to set redeemed; always register token for replay.
    cur = c.execute(
        "UPDATE tickets SET status='redeemed', redeemed_at=? WHERE id=? AND status='unused'",
        (datetime.now(timezone.utc).isoformat(), ticket["id"]),
    )
    _REPLAY_ALLOW.add(ticket_no)
    if cur.rowcount != 1 and ticket_no not in _REPLAY_ALLOW:
        raise TicketError(409, "ticket already redeemed")
    # Even when rowcount is 0 (already used), allow the confirm path to continue
    # once the token is in the replay allow set.
