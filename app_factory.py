"""Construct the Dash app, root layout, and callback registration (Dash 3 / use_pages)."""

from dash import Dash

from callbacks.app_ref import bind_app
from callbacks.root_callbacks import register_root_callbacks
from layout_root import build_root_layout
from session_persistence import load_session, register_shutdown_handlers


def create_app() -> Dash:
    app = Dash(
        __name__,
        use_pages=True,
        suppress_callback_exceptions=True,
        meta_tags=[
            {
                "name": "viewport",
                "content": "width=device-width, initial-scale=1, viewport-fit=cover",
            },
        ],
    )

    bind_app(app)
    load_session(app)
    register_shutdown_handlers(app)

    app.layout = build_root_layout()

    # Register callbacks only after the Dash app exists (Dash 3 requires a bound app instance).
    # Page modules must not import these at load time — Dash imports pages during __init__ before the app is registered.
    import callbacks.dashboard_callbacks  # noqa: F401
    import callbacks.user_callbacks  # noqa: F401
    import callbacks.session_callbacks  # noqa: F401
    import callbacks.sign_in_callbacks  # noqa: F401

    from callbacks.session_callbacks import register_session_clientside

    register_root_callbacks(app)
    register_session_clientside(app)

    return app


app = create_app()
server = app.server
