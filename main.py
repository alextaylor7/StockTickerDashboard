import logging
import socket

from waitress import serve

import constants
from app_factory import app, server

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 8050


def _guess_lan_ipv4() -> str | None:
    """Best-effort primary IPv4 for URLs other devices can use (same as outbound route)."""
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.connect(("8.8.8.8", 80))
            return probe.getsockname()[0]
        finally:
            probe.close()
    except OSError:
        pass
    try:
        host = socket.gethostname()
        ip = socket.gethostbyname(host)
        if ip and ip != "127.0.0.1":
            return ip
    except OSError:
        pass
    return None


def _print_startup_banner() -> None:
    local_url = f"http://127.0.0.1:{LISTEN_PORT}/"
    print(f"\n  This PC:     {local_url}", flush=True)
    lan = _guess_lan_ipv4()
    if lan and lan != "127.0.0.1":
        print(f"  Other devices: http://{lan}:{LISTEN_PORT}/", flush=True)
    else:
        print(
            f"  Other devices: use this machine's IPv4 in Network settings, port {LISTEN_PORT} "
            "(e.g. http://192.168.x.x:8050/)",
            flush=True,
        )
    print("  Logs and errors (INFO and above) follow. Ctrl+C to stop.\n", flush=True)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
        force=True,
    )
    # Threaded Waitress WSGI: handles many concurrent Dash clients (LAN parties). Single process
    # only — game state lives in server.config (see README). PyInstaller exe uses this block too.
    _print_startup_banner()
    serve(
        server,
        host=LISTEN_HOST,
        port=LISTEN_PORT,
        threads=constants.WAITRESS_THREADS,
    )
