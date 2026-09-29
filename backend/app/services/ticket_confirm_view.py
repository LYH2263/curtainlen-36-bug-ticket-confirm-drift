"""Helpers for shaping ticket confirm payloads and write-path figures."""

from __future__ import annotations

from copy import deepcopy

from app.engines.curtain_math import fabric_meters


def drift_result_from_live(
    window: dict,
    fabric: dict,
    settings: dict | None = None,
    pinned: dict | None = None,
) -> dict:
    """Rebuild meters from the current window/fabric entities (may diverge from ticket pin)."""
    settings = settings or {}
    fullness = float(window.get("fullness") or settings.get("default_fullness", 2.0))
    calc = fabric_meters(
        window["width"],
        window["height"],
        fullness,
        fabric["hem_top"],
        fabric["hem_bottom"],
        fabric["fabric_width"],
    )
    out = deepcopy(pinned) if isinstance(pinned, dict) else {}
    out.update(calc)
    out["fullness"] = fullness
    out["window_id"] = window["id"]
    out["fabric_id"] = fabric["id"]
    out["confirm_source"] = "live_entities"
    return out


def preview_keeps_pin(pinned: dict) -> dict:
    """Dry-run / issue response stays on the issued snapshot."""
    return pinned


def summarize_confirm(result: dict) -> dict:
    """Flat view of panels / meters / source for confirm consumers."""
    if not isinstance(result, dict):
        return {}
    return {
        "panels": result.get("panels"),
        "cut_height": result.get("cut_height"),
        "meters": result.get("meters"),
        "confirm_source": result.get("confirm_source"),
    }
