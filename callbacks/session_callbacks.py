import base64
import json
import time
from datetime import datetime

import dash
from dash import ClientsideFunction, Input, Output, State, dcc, no_update

from callbacks.app_ref import callback

from session_persistence import apply_payload_to_server, build_payload


def _parse_upload_contents(contents: str | None) -> dict:
    if not contents:
        raise ValueError("No file contents")
    _, content_string = contents.split(",", 1)
    decoded = base64.b64decode(content_string)
    data = json.loads(decoded.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


@callback(
    Output("session-download", "data"),
    Output("session-feedback", "children"),
    Input("session-save-btn", "n_clicks"),
    prevent_initial_call=True,
)
def save_session_download(n_clicks):
    if not n_clicks:
        return no_update, no_update
    try:
        app = dash.get_app()
        payload = build_payload(app.server)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_{ts}.json"
        body = json.dumps(payload, indent=2)
        return dcc.send_string(body, filename=filename), "Saved."
    except Exception as e:
        return no_update, f"Save failed: {e}"


@callback(
    Output("session-reload", "data"),
    Output("session-feedback", "children", allow_duplicate=True),
    Input("session-upload", "contents"),
    State("session-upload", "filename"),
    prevent_initial_call=True,
)
def load_session_upload(contents, _filename):
    if not contents:
        return no_update, no_update
    try:
        data = _parse_upload_contents(contents)
        apply_payload_to_server(dash.get_app().server, data)
        return time.time(), "Loaded."
    except (ValueError, json.JSONDecodeError, OSError) as e:
        return no_update, f"Load failed: {e}"
    except Exception as e:
        return no_update, f"Load failed: {e}"


def register_session_clientside(app):
    app.clientside_callback(
        ClientsideFunction("stock_ticker", "sessionLoadClick"),
        Output("session-load-dummy", "data"),
        Input("session-load-btn", "n_clicks"),
        prevent_initial_call=True,
    )
