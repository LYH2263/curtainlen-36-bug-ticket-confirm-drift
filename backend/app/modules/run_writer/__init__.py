"""写历史 run：确认入账时原样写入票面快照（与核销同事务）。

票面 panels / cut_height / meters 在签发瞬间已钉住；确认只做落库，
不得按当前窗实体或门幅重算改写，因此这里不读取现场 window/fabric。
"""
from datetime import datetime, timezone


def write_run(c, ticket):
    """按票面 payload 原样追加一条 calc_runs，返回新 run 编号。"""
    cur = c.execute(
        "INSERT INTO calc_runs(window_id,fabric_id,result_json,note,created_at) VALUES (?,?,?,?,?)",
        (
            ticket["window_id"], ticket["fabric_id"], ticket["payload_json"],
            "算料票 %s" % ticket["ticket_no"],
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    return int(cur.lastrowid)
