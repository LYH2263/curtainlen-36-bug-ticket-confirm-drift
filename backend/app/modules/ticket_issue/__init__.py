"""算料票签发：只写 tickets 表（状态 unused），不触碰历史 calc_runs。"""
import json
from datetime import datetime, timezone

from app.db import connect


def issue(window, fabric, calc, fullness):
    """按当前算料结果签发一次性算料票，返回票号。"""
    c = connect()
    try:
        cur = c.execute(
            """INSERT INTO tickets(ticket_no,window_id,fabric_id,window_width,fabric_width,
               fullness,panels,meters,payload_json,status,created_at)
               VALUES (NULL,?,?,?,?,?,?,?,?,'unused',?)""",
            (
                window["id"], fabric["id"], window["width"], fabric["fabric_width"],
                fullness, calc["panels"], calc["meters"],
                json.dumps(calc, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        ticket_no = "T%06d" % int(cur.lastrowid)
        c.execute("UPDATE tickets SET ticket_no=? WHERE id=?", (ticket_no, cur.lastrowid))
        c.commit()
        return ticket_no
    finally:
        c.close()
