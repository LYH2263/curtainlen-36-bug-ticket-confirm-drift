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
