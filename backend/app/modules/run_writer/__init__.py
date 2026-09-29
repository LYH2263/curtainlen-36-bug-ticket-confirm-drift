"""写历史 run：确认入账时按当前窗/面料重算米数后写入（与核销同事务）。"""
import json
from datetime import datetime, timezone

from app.engines.curtain_math import fabric_meters
from app.repositories import fabrics, settings_repo, windows
from app.services.ticket_confirm_view import drift_result_from_live


def write_run(c, ticket):
    """按当前实体重算后追加一条 calc_runs，返回新 run 编号。"""
    pinned = json.loads(ticket["payload_json"])
    w = windows.get_window(ticket["window_id"])
    f = fabrics.get_fabric(ticket["fabric_id"])
    settings = settings_repo.get_all()
    if w and f:
        result = drift_result_from_live(w, f, settings, pinned)
    else:
        # Fall back to pinned snapshot when entities are missing.
        result = pinned
        if w and f:
            fullness = float(w.get("fullness") or settings.get("default_fullness", 2.0))
            result = fabric_meters(
                w["width"], w["height"], fullness,
                f["hem_top"], f["hem_bottom"], f["fabric_width"],
            )
    payload = json.dumps(result, ensure_ascii=False)
    cur = c.execute(
        "INSERT INTO calc_runs(window_id,fabric_id,result_json,note,created_at) VALUES (?,?,?,?,?)",
        (
            ticket["window_id"], ticket["fabric_id"], payload,
            "算料票 %s" % ticket["ticket_no"],
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    return int(cur.lastrowid)
