"""Persist STOCK_PRICES and USER_STATE to data/session_state.json (atomic write)."""
from __future__ import annotations

import atexit
import json
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from constants import commodities

SESSION_PATH = Path(__file__).resolve().parent / "data" / "session_state.json"
VERSION = 1

_app_ref: Any = None


def _ensure_data_dir() -> None:
    SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)


def _default_stock_prices() -> dict[str, float]:
    return {c: 1.00 for c in commodities}


def _normalize_user_state(user_state: dict) -> dict:
    from callbacks.user_callbacks import _normalize_user_state as norm

    return norm(user_state)


def _normalize_user_state_map(raw: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not isinstance(raw, dict):
        return {}
    for key, val in raw.items():
        if not isinstance(key, str) or not isinstance(val, dict):
            continue
        out[key] = _normalize_user_state(val)
    return out


def _normalize_stock_prices(raw: Any) -> dict[str, float]:
    if not isinstance(raw, dict):
        return _default_stock_prices()
    return {c: round(float(raw.get(c, 1.00)), 2) for c in commodities}


def _sync_dashboard_module_prices(prices: dict[str, float]) -> None:
    import callbacks.dashboard_callbacks as dc

    dc.stock_prices = {c: prices[c] for c in commodities}


def build_payload(server) -> dict[str, Any]:
    """Snapshot dict for JSON (save file, download, crash snapshot)."""
    stock_prices = server.config.get("STOCK_PRICES")
    user_state = server.config.get("USER_STATE")

    if not isinstance(stock_prices, dict):
        stock_prices = _default_stock_prices()
    else:
        stock_prices = _normalize_stock_prices(stock_prices)

    if not isinstance(user_state, dict):
        user_state = {}
    else:
        user_state = _normalize_user_state_map(user_state)

    return {
        "version": VERSION,
        "stock_prices": stock_prices,
        "user_state": user_state,
    }


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    _ensure_data_dir()
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp_path, path)
    except OSError:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def apply_payload_to_server(server, data: Any) -> None:
    """Apply a loaded JSON dict to server.config and sync dashboard globals."""
    if not isinstance(data, dict):
        server.config["STOCK_PRICES"] = _default_stock_prices()
        server.config["USER_STATE"] = {}
        _sync_dashboard_module_prices(server.config["STOCK_PRICES"])
        return

    server.config["STOCK_PRICES"] = _normalize_stock_prices(data.get("stock_prices"))
    server.config["USER_STATE"] = _normalize_user_state_map(data.get("user_state") or {})
    _sync_dashboard_module_prices(server.config["STOCK_PRICES"])


def save_session(app=None, server=None) -> None:
    """Write current server.config STOCK_PRICES and USER_STATE to disk."""
    if app is not None:
        server = app.server
    if server is None:
        return

    payload = build_payload(server)
    _atomic_write_json(SESSION_PATH, payload)


def _crash_snapshot_path() -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return SESSION_PATH.parent / f"session_crash_{ts}.json"


def save_crash_snapshot(app=None, server=None) -> None:
    """Write a timestamped snapshot under data/ (unhandled exception only; see register_shutdown_handlers)."""
    if app is not None:
        server = app.server
    if server is None:
        return
    payload = build_payload(server)
    _atomic_write_json(_crash_snapshot_path(), payload)


def load_session(app=None, server=None) -> None:
    """Load session from default disk path into server.config."""
    if app is not None:
        server = app.server
    if server is None:
        return

    if not SESSION_PATH.is_file():
        if "STOCK_PRICES" not in server.config:
            server.config["STOCK_PRICES"] = _default_stock_prices()
        if "USER_STATE" not in server.config:
            server.config["USER_STATE"] = {}
        _sync_dashboard_module_prices(server.config["STOCK_PRICES"])
        return

    try:
        with open(SESSION_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        server.config.setdefault("STOCK_PRICES", _default_stock_prices())
        server.config.setdefault("USER_STATE", {})
        _sync_dashboard_module_prices(server.config["STOCK_PRICES"])
        return

    apply_payload_to_server(server, data)


def register_shutdown_handlers(app) -> None:
    """Persist session on normal exit; crash snapshots only on fatal unhandled exceptions."""
    global _app_ref
    _app_ref = app

    _original_excepthook = sys.excepthook

    def _excepthook(exc_type, exc_value, exc_traceback):
        # Only snapshot when the process is about to die from an unhandled Exception
        # (not KeyboardInterrupt/SystemExit, not normal shutdown, not caught callback errors).
        try:
            if (
                exc_type is not None
                and isinstance(exc_type, type)
                and issubclass(exc_type, Exception)
            ):
                save_crash_snapshot(_app_ref)
        except Exception:
            pass
        _original_excepthook(exc_type, exc_value, exc_traceback)

    sys.excepthook = _excepthook

    def _flush():
        try:
            save_session(_app_ref)
        except Exception:
            pass

    atexit.register(_flush)

    def _on_signal(signum, frame):
        _flush()
        sys.exit(0)

    try:
        signal.signal(signal.SIGINT, _on_signal)
    except (ValueError, OSError):
        pass
    if hasattr(signal, "SIGTERM"):
        try:
            signal.signal(signal.SIGTERM, _on_signal)
        except (ValueError, OSError):
            pass
