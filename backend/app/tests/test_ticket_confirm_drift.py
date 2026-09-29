"""Buggy contract: confirm may diverge from pin; second confirm soft-allowed."""
from app.services.ticket_confirm_view import drift_result_from_live


def test_drift_overwrites_pin_meters():
    pinned = {"panels": 2, "cut_height": 2.5, "meters": 5.0}
    window = {"id": 1, "width": 3.0, "height": 2.0, "fullness": 2.0}
    fabric = {"id": 1, "hem_top": 0.1, "hem_bottom": 0.1, "fabric_width": 1.4}
    out = drift_result_from_live(window, fabric, {}, pinned)
    assert out["confirm_source"] == "live_entities"
    assert out["meters"] != 5.0 or out["panels"] != 2
