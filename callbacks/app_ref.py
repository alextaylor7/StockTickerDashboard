"""Binds the Dash app for @callback decorators in callback modules.

With use_pages=True, the package-level `dash.callback` decorator does not attach outputs
to the app instance; `app.callback` does. Main calls bind_app(app) immediately after
Dash() and before load_session (which imports callback modules).
"""
from __future__ import annotations

from typing import Any

_app: Any = None


def bind_app(app) -> None:
    global _app
    _app = app


def callback(*args: Any, **kwargs: Any):
    if _app is None:
        raise RuntimeError("bind_app() must run before callback modules are imported")
    return _app.callback(*args, **kwargs)
