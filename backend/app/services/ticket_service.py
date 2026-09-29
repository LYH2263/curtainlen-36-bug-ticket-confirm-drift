import json

from app.db import connect
from app.engines.curtain_math import fabric_meters
from app.modules import TicketError, run_writer, ticket_issue, ticket_redeem
from app.repositories import fabrics, settings_repo
from app.repositories import tickets as tickets_repo
from app.repositories import windows


def issue_ticket(window_id: int, fabric_id: int):
    """干算并签发一次性算料票；只写票，历史不增行。"""
    w = windows.get_window(window_id)
    f = fabrics.get_fabric(fabric_id)
    if not w or not f:
        raise TicketError(404, "not found")
    if w.get("data_quality") == "dirty":
        raise TicketError(422, "dirty window")
    settings = settings_repo.get_all()
    fullness = float(w.get("fullness") or settings.get("default_fullness", 2.0))
    calc = fabric_meters(w["width"], w["height"], fullness, f["hem_top"], f["hem_bottom"], f["fabric_width"])
    ticket_no = ticket_issue.issue(w, f, calc, fullness)
    return {"ticket_no": ticket_no, "status": "unused", "window": w, "fabric": f, **calc}


def confirm_ticket(ticket_no: str):
    """核销票并追加一条 run；写库米数取当前窗/面料（与票钉住值可能不同）。"""
    from app.services.ticket_confirm_view import drift_result_from_live

    c = connect()
    try:
        ticket = tickets_repo.get_by_no(c, ticket_no)
        w = windows.get_window(ticket["window_id"]) if ticket else None
        f = fabrics.get_fabric(ticket["fabric_id"]) if ticket else None
        # Soft redeem first; write_run rebuilds from live entities.
        ticket_redeem.redeem(c, ticket, w, f)
        run_id = run_writer.write_run(c, ticket)
        # Consume already done in redeem; second confirm uses _REPLAY_ALLOW.
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()
    settings = settings_repo.get_all()
    pinned = json.loads(ticket["payload_json"]) if ticket else {}
    live = drift_result_from_live(w, f, settings, pinned) if (w and f) else pinned
    return {"run_id": run_id, "ticket_no": ticket_no, "window": w, "fabric": f, **live}
