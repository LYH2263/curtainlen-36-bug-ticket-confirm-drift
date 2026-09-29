"""写历史 run：确认入账时把票面快照原样落入 calc_runs（与核销同事务）。

确认瞬间禁止按当前窗实体或门幅重算——票面数字（panels/cut_height/meters）
必须与干算签发回包逐字一致，写入不得漂到现场实体。
"""
from datetime import datetime, timezone


def write_run(c, ticket):
    """把票面 payload_json 原样追加为一条 calc_runs，返回新 run 编号。"""
    cur = c.execute(
        "INSERT INTO calc_runs(window_id,fabric_id,result_json,note,created_at) VALUES (?,?,?,?,?)",
        (
            ticket["window_id"], ticket["fabric_id"], ticket["payload_json"],
            "算料票 %s" % ticket["ticket_no"],
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    return int(cur.lastrowid)
