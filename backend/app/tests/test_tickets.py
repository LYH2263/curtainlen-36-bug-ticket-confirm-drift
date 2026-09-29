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
    # 签发只写票，历史表行数不得增加
    assert history.count_runs() == before
    t = tickets_repo.get(r["ticket_no"])
    assert t["status"] == "unused"
    # 票面 panels/meters 与干算回包一致
    assert t["panels"] == r["panels"] == 5
    assert t["meters"] == r["meters"] == 14.25
    # cut_height 钉在 payload 里，同样与回包一致
    import json
    assert json.loads(t["payload_json"])["cut_height"] == r["cut_height"] == 2.85


def test_confirm_appends_run_with_pinned_values(db):
    issued = ticket_service.issue_ticket(1, 1)
    ticket_no = issued["ticket_no"]
    pinned = {"panels": issued["panels"], "cut_height": issued["cut_height"], "meters": issued["meters"]}
    # 签发后改了窗高（非窗宽/门幅）：确认仍成功，但数字不得在确认瞬间重算
    _update("UPDATE windows SET height=? WHERE id=?", 9.9, 1)
    r = ticket_service.confirm_ticket(ticket_no)
    assert history.count_runs() == 1
    run = history.list_runs(1)[0]
    assert run["id"] == r["run_id"]
    # 落库 run 的 panels/cut_height/meters 原样等于票面
    for k, v in pinned.items():
        assert run["result"][k] == v
        assert r[k] == v
    assert tickets_repo.get(ticket_no)["status"] == "redeemed"


def test_second_confirm_fails_without_new_row(db):
    ticket_no = ticket_service.issue_ticket(1, 1)["ticket_no"]
    ticket_service.confirm_ticket(ticket_no)
    before = history.count_runs()
    with pytest.raises(TicketError) as e:
        ticket_service.confirm_ticket(ticket_no)
    assert e.value.status_code == 409
    # 同一票再次确认报冲突且不再增行
    assert history.count_runs() == before
    assert tickets_repo.get(ticket_no)["status"] == "redeemed"


def test_confirm_fails_if_window_width_changed(db):
    ticket_no = ticket_service.issue_ticket(1, 1)["ticket_no"]
    _update("UPDATE windows SET width=? WHERE id=?", 3.3, 1)
    with pytest.raises(TicketError) as e:
        ticket_service.confirm_ticket(ticket_no)
    assert e.value.status_code == 409
    # 窗宽被改过：拒绝且不增行，票仍未核销
    assert history.count_runs() == 0
    assert tickets_repo.get(ticket_no)["status"] == "unused"


def test_confirm_fails_if_fabric_width_changed(db):
    ticket_no = ticket_service.issue_ticket(1, 1)["ticket_no"]
    _update("UPDATE fabrics SET fabric_width=? WHERE id=?", 1.5, 1)
    with pytest.raises(TicketError) as e:
        ticket_service.confirm_ticket(ticket_no)
    assert e.value.status_code == 409
    # 门幅被改过：拒绝且不增行，票仍未核销
    assert history.count_runs() == 0
    assert tickets_repo.get(ticket_no)["status"] == "unused"


def test_confirmed_run_opens_with_ticket_figures_even_after_entity_drift(db):
    issued = ticket_service.issue_ticket(1, 1)
    pinned = {"panels": issued["panels"], "cut_height": issued["cut_height"], "meters": issued["meters"]}
    r = ticket_service.confirm_ticket(issued["ticket_no"])

    # 确认之后窗宽、窗高、门幅全部被改动
    _update("UPDATE windows SET width=?, height=? WHERE id=?", 8.8, 9.9, 1)
    _update("UPDATE fabrics SET fabric_width=?, hem_top=?, hem_bottom=? WHERE id=?", 2.2, 0.9, 0.9, 1)

    # 从历史打开该编号，仍只能看见票面那一组数字
    opened = history.get_run(r["run_id"])
    for k, v in pinned.items():
        assert opened["result"][k] == v

    # 再干算一张新票并确认，不得改写已确认旧 run
    second = ticket_service.issue_ticket(1, 2)
    ticket_service.confirm_ticket(second["ticket_no"])
    assert history.count_runs() == 2
    reopened = history.get_run(r["run_id"])
    for k, v in pinned.items():
        assert reopened["result"][k] == v


def test_preview_and_confirm_write_corroborate(db):
    # 干算预览钉住签发快照：先记下回包，之后什么都不改，确认写入须与预览逐字段相同
    issued = ticket_service.issue_ticket(1, 1)
    confirmed = ticket_service.confirm_ticket(issued["ticket_no"])
    for k in ("panels", "cut_height", "meters"):
        assert confirmed[k] == issued[k]
    stored = history.get_run(confirmed["run_id"])["result"]
    for k in ("panels", "cut_height", "meters"):
        assert stored[k] == issued[k]


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
