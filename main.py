#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Coding Companion — Daemon entry point.
Starts the hook server that listens for Claude Code events,
tracks session state, and sends Feishu notifications.

Usage:
  python main.py              # Start daemon (foreground)
  python main.py --once       # Start daemon, run once, exit
  python main.py --status     # Check if daemon is already running
"""

import sys
import os
import time
import signal
import io

# Windows encoding setup
if sys.platform == "win32":
    os.environ["PYTHONUNBUFFERED"] = "1"
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding="utf-8",
        errors="replace",
        line_buffering=True,
        write_through=True,
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer,
        encoding="utf-8",
        errors="replace",
        line_buffering=True,
        write_through=True,
    )

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.hook_server import HookServer
from src.notifier import Notifier
from src.utils import load_config


PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".companion.pid")


def main():
    config = load_config("config.yaml")
    if not config:
        print("ERROR: Cannot load config.yaml")
        return 1

    # Write PID file
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    # Init notifier
    notification_config = config.get("notification", {})
    notifier = Notifier(notification_config.get("channels", []))

    # Init and start hook server
    server = HookServer(config)
    server.set_notifier(notifier)
    server.start()

    host = config['daemon']['host']
    port = config['daemon']['port']
    dashboard_url = f"http://{host}:{port}"

    print(f"\nAI Coding Companion v{config.get('version', '3.0')}")
    print(f"Dashboard: {dashboard_url}")
    print(f"Projects: {len(config.get('projects', []))}")
    print(f"Notification: {'enabled' if notification_config.get('enabled', True) else 'disabled'}")
    print(f"Inactivity timeout: {config['daemon'].get('inactivity_timeout', 300)}s")
    print()

    # Try to open browser (unless --no-browser is specified)
    if "--no-browser" not in sys.argv:
        try:
            import webbrowser
            webbrowser.open(dashboard_url)
        except Exception:
            pass

    running = True

    def signal_handler(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while running:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        _cleanup_pid()
        print("Daemon stopped.")

    return 0


def _cleanup_pid():
    try:
        os.remove(PID_FILE)
    except OSError:
        pass


if __name__ == "__main__":
    sys.exit(main())
