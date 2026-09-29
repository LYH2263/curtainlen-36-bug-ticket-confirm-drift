import json

import pytest

from app import seed
from app.db import connect
from app.modules import TicketError
from app.repositories import history
from app.repositories import tickets as tickets_repo
from app.services import ticket_service


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setattr("app.db.DB_PATH", tmp_path / "test.db")
    seed.init_db()
    return tmp_path / "test.db"


def _update(sql, *args):
    c = connect()
    try:
        c.execute(sql, args)
        c.commit()
    finally:
        c.close()


def test_issue_writes_no_history(db):
    before = history.count_runs()
    r = ticket_service.issue_ticket(1, 1)
    assert history.count_runs() == before
    t = tickets_repo.get(r["ticket_no"])
    assert t["status"] == "unused"
    assert t["panels"] == r["panels"] == 5
    assert t["meters"] == r["meters"] == 14.25
    # 票面 panels/cut_height/meters 与干算回包一致，且整张快照逐字落票
    assert r["cut_height"] == 2.85
    assert json.loads(t["payload_json"]) == {
        "finished_width": r["finished_width"],
        "panels": r["panels"],
        "cut_height": r["cut_height"],
        "meters": r["meters"],
        "fabric_width": r["fabric_width"],
    }


def test_confirm_appends_run_with_pinned_values(db):
    ticket_no = ticket_service.issue_ticket(1, 1)["ticket_no"]
    # 签发后改了窗高（非窗宽/门幅）：确认仍成功，run 钉住票内 panels/meters 而非重算
    _update("UPDATE windows SET height=? WHERE id=?", 9.9, 1)
    r = ticket_service.confirm_ticket(ticket_no)
    assert history.count_runs() == 1
    run = history.list_runs(1)[0]
    assert run["id"] == r["run_id"]
    assert run["result"]["panels"] == 5
    assert run["result"]["meters"] == 14.25
    assert tickets_repo.get(ticket_no)["status"] == "redeemed"


def test_confirm_response_and_stored_run_equal_ticket_face(db):
    issued = ticket_service.issue_ticket(1, 1)
    face = {k: issued[k] for k in ("panels", "cut_height", "meters")}
    # 确认瞬间窗实体已变（高度），回包仍须等于票面
    _update("UPDATE windows SET height=? WHERE id=?", 7.7, 1)
    confirmed = ticket_service.confirm_ticket(issued["ticket_no"])
    assert {k: confirmed[k] for k in ("panels", "cut_height", "meters")} == face
    # 新 run 的 result_json 与票 payload_json 逐字相同
    c = connect()
    try:
        row = c.execute("SELECT result_json FROM calc_runs WHERE id=?",
                        (confirmed["run_id"],)).fetchone()
        ticket_row = c.execute("SELECT payload_json FROM tickets WHERE ticket_no=?",
                               (issued["ticket_no"],)).fetchone()
    finally:
        c.close()
    assert row["result_json"] == ticket_row["payload_json"]
    opened = history.get_run(confirmed["run_id"])
    assert {k: opened["result"][k] for k in ("panels", "cut_height", "meters")} == face


def test_history_entry_keeps_face_after_width_and_fabric_change(db):
    issued = ticket_service.issue_ticket(1, 1)
    face = {k: issued[k] for k in ("panels", "cut_height", "meters")}
    confirmed = ticket_service.confirm_ticket(issued["ticket_no"])
    # 确认成功后窗宽、门幅都被改过：从历史打开仍只能看见票面那一组数字
    _update("UPDATE windows SET width=? WHERE id=?", 5.0, 1)
    _update("UPDATE fabrics SET fabric_width=? WHERE id=?", 2.8, 1)
    opened = history.get_run(confirmed["run_id"])
    assert {k: opened["result"][k] for k in ("panels", "cut_height", "meters")} == face
    assert history.count_runs() == 1


def test_new_issue_after_confirm_does_not_rewrite_old_run(db):
    first = ticket_service.issue_ticket(1, 1)
    old_face = {k: first[k] for k in ("panels", "cut_height", "meters")}
    old_run = ticket_service.confirm_ticket(first["ticket_no"])["run_id"]
    # 改窗宽门幅后再干算一张新票并确认，旧 run 的数字不得被改写
    _update("UPDATE windows SET width=? WHERE id=?", 2.2, 1)
    second = ticket_service.issue_ticket(2, 2)
    ticket_service.confirm_ticket(second["ticket_no"])
    assert history.count_runs() == 2
    opened = history.get_run(old_run)
    assert {k: opened["result"][k] for k in ("panels", "cut_height", "meters")} == old_face


def test_failed_drift_confirm_leaves_ticket_unused_and_reusable(db):
    ticket_no = ticket_service.issue_ticket(1, 1)["ticket_no"]
    _update("UPDATE windows SET width=? WHERE id=?", 3.3, 1)
    with pytest.raises(TicketError) as e:
        ticket_service.confirm_ticket(ticket_no)
    assert e.value.status_code == 409
    # 漂移拒绝不得产生半核销：恢复窗宽后同票仍可确认且只增一行
    _update("UPDATE windows SET width=? WHERE id=?", 3.0, 1)
    ticket_service.confirm_ticket(ticket_no)
    assert history.count_runs() == 1
    assert tickets_repo.get(ticket_no)["status"] == "redeemed"


def test_second_confirm_fails_without_new_row(db):
    ticket_no = ticket_service.issue_ticket(1, 1)["ticket_no"]
    ticket_service.confirm_ticket(ticket_no)
    before = history.count_runs()
    with pytest.raises(TicketError) as e:
        ticket_service.confirm_ticket(ticket_no)
    assert e.value.status_code == 409
    assert history.count_runs() == before
    assert tickets_repo.get(ticket_no)["status"] == "redeemed"


def test_confirm_fails_if_window_width_changed(db):
    ticket_no = ticket_service.issue_ticket(1, 1)["ticket_no"]
    _update("UPDATE windows SET width=? WHERE id=?", 3.3, 1)
    with pytest.raises(TicketError) as e:
        ticket_service.confirm_ticket(ticket_no)
    assert e.value.status_code == 409
    assert history.count_runs() == 0
    assert tickets_repo.get(ticket_no)["status"] == "unused"


def test_confirm_fails_if_fabric_width_changed(db):
    ticket_no = ticket_service.issue_ticket(1, 1)["ticket_no"]
    _update("UPDATE fabrics SET fabric_width=? WHERE id=?", 1.5, 1)
    with pytest.raises(TicketError) as e:
        ticket_service.confirm_ticket(ticket_no)
    assert e.value.status_code == 409
    assert history.count_runs() == 0
    assert tickets_repo.get(ticket_no)["status"] == "unused"


def test_confirm_unknown_ticket_404(db):
    with pytest.raises(TicketError) as e:
        ticket_service.confirm_ticket("T999999")
    assert e.value.status_code == 404
    assert history.count_runs() == 0


def test_issue_dirty_window_rejected(db):
    with pytest.raises(TicketError) as e:
        ticket_service.issue_ticket(3, 1)
    assert e.value.status_code == 422
    assert tickets_repo.count() == 0
