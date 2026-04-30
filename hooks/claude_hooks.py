#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code hook forwarder.
Called by Claude Code hooks (Stop, UserPromptSubmit, PostToolUse).
Reads hook context from stdin (JSON) and POSTs it to the companion daemon.

Usage (in ~/.claude/settings.json):
  "hooks": {
    "Stop": [{"command": "python hooks/claude_hooks.py stop"}],
    "UserPromptSubmit": [{"command": "python hooks/claude_hooks.py user-submit"}]
  }
"""

import sys
import json
import os
import urllib.request
import urllib.error

# Companion daemon URL
DAEMON_URL = os.environ.get("COMPANION_DAEMON_URL", "http://127.0.0.1:9599")


def read_hook_context() -> dict:
    """Read the hook context from stdin (Claude Code passes it as JSON)."""
    try:
        raw = sys.stdin.read()
        if raw:
            return json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    return {}


def post_event(event_type: str, context: dict) -> bool:
    """POST the hook event to the companion daemon."""
    url = f"{DAEMON_URL}/hook/{event_type}"

    # Add CWD as project_path if not already present
    if "project_path" not in context:
        context["project_path"] = os.getcwd()

    data = json.dumps(context, ensure_ascii=False).encode("utf-8")

    try:
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except urllib.error.URLError:
        # Daemon not running — fail silently, don't block Claude Code
        return False
    except Exception:
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: claude_hooks.py <stop|user-submit|post-tool>", file=sys.stderr)
        sys.exit(1)

    event_type = sys.argv[1]
    if event_type not in ("stop", "user-submit", "permission-request", "post-tool"):
        print(f"Unknown event type: {event_type}", file=sys.stderr)
        sys.exit(1)

    context = read_hook_context()
    success = post_event(event_type, context)

    if not success:
        # Silent failure — don't block Claude Code
        # The daemon might not be running, that's OK
        pass

    sys.exit(0 if success else 0)  # Always exit 0 to not block Claude


if __name__ == "__main__":
    main()
