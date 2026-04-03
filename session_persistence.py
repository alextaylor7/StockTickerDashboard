"""Persist STOCK_PRICES, USER_STATE, TURN_COUNT, game length, turn timeline, turn-roll timing, dice feeds."""
from __future__ import annotations

import atexit
import json
import os
import signal
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from constants import COMMODITIES, DEFAULT_GAME_MAX_TURNS, SESSION_SAVE_DEBOUNCE_SEC
from domain.user_state import normalize_user_state


def _runtime_base_dir() -> Path:
    """Return writable runtime base folder for session files."""
    # PyInstaller/other frozen builds: keep data beside the executable.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # Source run: keep existing repo-local behavior.
    return Path(__file__).resolve().parent


SESSION_PATH = _runtime_base_dir() / "data" / "session_state.json"
# v1: turn_count was completed-turn count (0,1,…). v2: turn_count is the next/current turn label (1,2,…).
# v3: optional turn_timeline (per-turn snapshots for dashboard graphs).
# v4: optional turn_roll_interval_sec (integer seconds between dice rolls in a turn).
# v5: optional current_turn_rolls / last_turn_rolls (dice feed; list of {commodity, action, value}).
# v6: optional game_max_turns (end play when TURN_COUNT exceeds this).
VERSION = 6

_app_ref: Any = None


def _ensure_data_dir() -> None:
    SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)


def _default_stock_prices() -> dict[str, float]:
    return {c: 1.00 for c in COMMODITIES}


def _normalize_user_state_map(raw: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not isinstance(raw, dict):
        return {}
    for key, val in raw.items():
        if not isinstance(key, str) or not isinstance(val, dict):
            continue
        out[key] = normalize_user_state(val)
    return out


def _normalize_stock_prices(raw: Any) -> dict[str, float]:
    if not isinstance(raw, dict):
        return _default_stock_prices()
    return {c: round(float(raw.get(c, 1.00)), 2) for c in COMMODITIES}


def _normalize_turn_timeline(raw: Any) -> list[dict[str, Any]]:
    """List of {turn, stock_prices, player_net} for each completed turn."""
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            turn = int(item.get("turn"))
        except (TypeError, ValueError):
            continue
        sp_in = item.get("stock_prices")
        if not isinstance(sp_in, dict):
            sp_in = {}
        stock_prices = {c: round(float(sp_in.get(c, 1.00)), 2) for c in COMMODITIES}
        pn_in = item.get("player_net")
        player_net: dict[str, float] = {}
        if isinstance(pn_in, dict):
            for k, v in pn_in.items():
                if not isinstance(k, str):
                    continue
                try:
                    player_net[k] = round(float(v), 2)
                except (TypeError, ValueError):
                    pass
        out.append({"turn": turn, "stock_prices": stock_prices, "player_net": player_net})
    return out


def _normalize_turn_count(raw: Any) -> int:
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return 0


def _normalize_next_turn_label(raw: Any) -> int:
    """1-based turn number shown on the Play button (minimum 1)."""
    try:
        return max(1, int(raw))
    except (TypeError, ValueError):
        return 1


def _normalize_turn_roll_interval_sec(raw: Any) -> int:
    """Whole seconds between automatic rolls during a multi-player turn (clamped)."""
    try:
        v = int(float(raw))
    except (TypeError, ValueError):
        v = 1
    return max(1, min(600, v))


def _normalize_game_max_turns(raw: Any) -> int:
    """Maximum playable turn label inclusive; clamped 1..999; default when missing/invalid."""
    try:
        v = int(float(raw))
    except (TypeError, ValueError):
        v = DEFAULT_GAME_MAX_TURNS
    return max(1, min(999, v))


def _normalize_turn_roll_feed_list(raw: Any) -> list[dict[str, str]]:
    """List of {commodity, action, value} for dashboard dice feed persistence."""
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        c = item.get("commodity")
        a = item.get("action")
        if not isinstance(c, str) or not isinstance(a, str):
            continue
        v = item.get("value")
        out.append({"commodity": c, "action": a, "value": str(v) if v is not None else ""})
    return out


def _turn_count_from_saved_payload(data: dict) -> int:
    """Map JSON turn_count to server TURN_COUNT (button label; 1-based)."""
    file_ver = int(data.get("version", 1))
    raw = data.get("turn_count")
    if file_ver < 2:
        completed = _normalize_turn_count(raw)
        return max(1, completed + 1)
    if raw is None:
        return 1
    return _normalize_next_turn_label(raw)


def _sync_dashboard_module_prices(prices: dict[str, float]) -> None:
    import callbacks.dashboard_callbacks as dc

    dc.stock_prices = {c: prices[c] for c in COMMODITIES}


def _sync_dashboard_module_prices_to_server(server) -> None:
    """Copy live dashboard module prices into server.config before persisting."""
    try:
        import callbacks.dashboard_callbacks as dc

        if isinstance(getattr(dc, "stock_prices", None), dict):
            server.config["STOCK_PRICES"] = {
                c: round(float(dc.stock_prices.get(c, 1.00)), 2) for c in COMMODITIES
            }
    except Exception:
        pass


def _session_payload_is_empty_game_state(payload: dict[str, Any]) -> bool:
    """True if snapshot has no users and all commodity prices are par ($1)."""
    us = payload.get("user_state") or {}
    if not isinstance(us, dict) or len(us) > 0:
        return False
    sp = payload.get("stock_prices") or {}
    if not isinstance(sp, dict):
        return True
    return all(round(float(sp.get(c, 1.0)), 2) == 1.0 for c in COMMODITIES)


def _would_clobber_saved_session_with_empty_runtime(
    proposed: dict[str, Any], existing_file: dict[str, Any] | None
) -> bool:
    """Werkzeug reloader parent exits with empty server.config — do not overwrite a real session."""
    if not existing_file or not isinstance(existing_file, dict):
        return False
    if not _session_payload_is_empty_game_state(proposed):
        return False
    old_us = existing_file.get("user_state") or {}
    if isinstance(old_us, dict) and len(old_us) > 0:
        return True
    old_sp = existing_file.get("stock_prices") or {}
    if isinstance(old_sp, dict):
        for c in COMMODITIES:
            if round(float(old_sp.get(c, 1.0)), 2) != 1.0:
                return True
    return False


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

    turn_count = _normalize_next_turn_label(server.config.get("TURN_COUNT", 1))

    turn_timeline = server.config.get("TURN_TIMELINE")
    if not isinstance(turn_timeline, list):
        turn_timeline = []
    else:
        turn_timeline = _normalize_turn_timeline(turn_timeline)

    turn_roll_interval_sec = _normalize_turn_roll_interval_sec(
        server.config.get("TURN_ROLL_INTERVAL_SEC")
    )

    current_turn_rolls = _normalize_turn_roll_feed_list(server.config.get("CURRENT_TURN_ROLLS"))
    last_turn_rolls = _normalize_turn_roll_feed_list(server.config.get("LAST_TURN_ROLLS"))

    game_max_turns = _normalize_game_max_turns(server.config.get("GAME_MAX_TURNS"))

    return {
        "version": VERSION,
        "stock_prices": stock_prices,
        "user_state": user_state,
        "turn_count": turn_count,
        "turn_timeline": turn_timeline,
        "turn_roll_interval_sec": turn_roll_interval_sec,
        "current_turn_rolls": current_turn_rolls,
        "last_turn_rolls": last_turn_rolls,
        "game_max_turns": game_max_turns,
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
        server.config["TURN_COUNT"] = 1
        server.config["TURN_TIMELINE"] = []
        server.config["TURN_ROLL_INTERVAL_SEC"] = _normalize_turn_roll_interval_sec(None)
        server.config["CURRENT_TURN_ROLLS"] = []
        server.config["LAST_TURN_ROLLS"] = []
        server.config["GAME_MAX_TURNS"] = _normalize_game_max_turns(None)
        _sync_dashboard_module_prices(server.config["STOCK_PRICES"])
        return

    server.config["STOCK_PRICES"] = _normalize_stock_prices(data.get("stock_prices"))
    server.config["USER_STATE"] = _normalize_user_state_map(data.get("user_state") or {})
    server.config["TURN_COUNT"] = _turn_count_from_saved_payload(data)
    server.config["TURN_TIMELINE"] = _normalize_turn_timeline(data.get("turn_timeline"))
    server.config["TURN_ROLL_INTERVAL_SEC"] = _normalize_turn_roll_interval_sec(
        data.get("turn_roll_interval_sec")
    )
    server.config["CURRENT_TURN_ROLLS"] = _normalize_turn_roll_feed_list(
        data.get("current_turn_rolls")
    )
    server.config["LAST_TURN_ROLLS"] = _normalize_turn_roll_feed_list(data.get("last_turn_rolls"))
    server.config["GAME_MAX_TURNS"] = _normalize_game_max_turns(data.get("game_max_turns"))
    _sync_dashboard_module_prices(server.config["STOCK_PRICES"])


def save_session(app=None, server=None) -> None:
    """Write current server.config STOCK_PRICES, USER_STATE, and TURN_COUNT to disk."""
    if app is not None:
        server = app.server
    if server is None:
        return

    _sync_dashboard_module_prices_to_server(server)
    payload = build_payload(server)
    _atomic_write_json(SESSION_PATH, payload)


_debounce_lock = threading.Lock()
_debounce_timer: threading.Timer | None = None


def cancel_debounced_save() -> None:
    """Cancel a pending debounced save (e.g. before shutdown flush)."""
    global _debounce_timer
    with _debounce_lock:
        if _debounce_timer is not None:
            _debounce_timer.cancel()
            _debounce_timer = None


def schedule_debounced_save(app, delay_sec: float | None = None) -> None:
    """Coalesce rapid trade saves into one disk write after a short quiet period."""
    global _debounce_timer
    if delay_sec is None:
        delay_sec = SESSION_SAVE_DEBOUNCE_SEC

    def _run():
        global _debounce_timer
        with _debounce_lock:
            _debounce_timer = None
        save_session(app)

    with _debounce_lock:
        if _debounce_timer is not None:
            _debounce_timer.cancel()
        _debounce_timer = threading.Timer(delay_sec, _run)
        _debounce_timer.daemon = True
        _debounce_timer.start()


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
        server.config.setdefault("TURN_COUNT", 1)
        server.config.setdefault("TURN_TIMELINE", [])
        server.config.setdefault(
            "TURN_ROLL_INTERVAL_SEC", _normalize_turn_roll_interval_sec(None)
        )
        server.config.setdefault("CURRENT_TURN_ROLLS", [])
        server.config.setdefault("LAST_TURN_ROLLS", [])
        server.config.setdefault("GAME_MAX_TURNS", _normalize_game_max_turns(None))
        _sync_dashboard_module_prices(server.config["STOCK_PRICES"])
        return

    try:
        with open(SESSION_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        server.config.setdefault("STOCK_PRICES", _default_stock_prices())
        server.config.setdefault("USER_STATE", {})
        server.config.setdefault("TURN_COUNT", 1)
        server.config.setdefault("TURN_TIMELINE", [])
        server.config.setdefault(
            "TURN_ROLL_INTERVAL_SEC", _normalize_turn_roll_interval_sec(None)
        )
        server.config.setdefault("CURRENT_TURN_ROLLS", [])
        server.config.setdefault("LAST_TURN_ROLLS", [])
        server.config.setdefault("GAME_MAX_TURNS", _normalize_game_max_turns(None))
        _sync_dashboard_module_prices(server.config["STOCK_PRICES"])
        return

    apply_payload_to_server(server, data)


def register_shutdown_handlers(app) -> None:
    """Persist session on normal exit; crash snapshots only on fatal unhandled exceptions."""
    global _app_ref
    _app_ref = app

    def _flush():
        try:
            import dash

            app = dash.get_app()
            if app is None:
                app = _app_ref
            if app is None:
                return
            cancel_debounced_save()
            server = app.server
            _sync_dashboard_module_prices_to_server(server)
            proposed = build_payload(server)
            if SESSION_PATH.is_file():
                try:
                    with open(SESSION_PATH, encoding="utf-8") as f:
                        existing = json.load(f)
                except (OSError, json.JSONDecodeError):
                    existing = None
                if _would_clobber_saved_session_with_empty_runtime(proposed, existing):
                    return
            save_session(app)
        except Exception:
            pass

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
