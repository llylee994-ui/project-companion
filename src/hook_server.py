# -*- coding: utf-8 -*-
"""
Lightweight HTTP server that receives Claude Code hook events.
Listens on localhost for POST events from hooks/claude_hooks.py forwarder.
"""

import json
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from .session import SessionManager
from .git_summary import get_session_summary


class HookHandler(BaseHTTPRequestHandler):
    """HTTP handler for Claude Code hook events."""

    # Set by HookServer at startup
    session_manager: SessionManager = None
    notifier = None
    config: dict = None
    known_projects: dict = {}  # path -> name mapping

    def log_message(self, format, *args):
        """Suppress default HTTP logging to stdout."""
        pass

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/status":
            self._json_response(200, {
                "status": "running",
                "sessions": self.session_manager.list_sessions(),
            })
        elif parsed.path == "/health":
            self._json_response(200, {"ok": True})
        else:
            self._json_response(404, {"error": "not found"})

    def do_POST(self):
        parsed = urlparse(self.path)

        # Read body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""
        data = self._parse_body(body)

        if parsed.path == "/hook/stop":
            self._handle_stop(data)
        elif parsed.path == "/hook/user-submit":
            self._handle_user_submit(data)
        elif parsed.path == "/hook/permission-request":
            self._handle_permission_request(data)
        elif parsed.path == "/hook/post-tool":
            self._handle_post_tool(data)
        elif parsed.path == "/hook/reload":
            self._handle_reload(data)
        else:
            self._json_response(404, {"error": "unknown hook endpoint"})

    def _handle_stop(self, data: dict):
        """Claude finished a response — start inactivity timer for completion detection."""
        project_name = self._resolve_project(data)

        session = self.session_manager.get_or_create(
            project_name,
            data.get("project_path", data.get("cwd", ".")),
        )
        session.on_stop()

        self._json_response(200, {
            "ok": True,
            "state": session.get_state(),
        })

    def _handle_permission_request(self, data: dict):
        """Claude Code is showing a permission dialog (desktop + terminal both)."""
        project_name = self._resolve_project(data)
        tool_name = data.get("tool_name", "unknown")
        tool_input = data.get("tool_input", {})

        session = self.session_manager.get_or_create(
            project_name,
            data.get("project_path", data.get("cwd", ".")),
        )
        session.on_permission_request(tool_name, tool_input)

        self._json_response(200, {
            "ok": True,
            "state": session.get_state(),
        })

    def _handle_user_submit(self, data: dict):
        """User submitted a new prompt."""
        project_name = self._resolve_project(data)

        session = self.session_manager.get_or_create(
            project_name,
            data.get("project_path", data.get("cwd", ".")),
        )
        session.on_user_submit()

        self._json_response(200, {
            "ok": True,
            "state": session.get_state(),
        })

    def _handle_post_tool(self, data: dict):
        """A tool was executed — could be used for progress tracking."""
        project_name = self._resolve_project(data)
        tool_name = data.get("tool_name", "unknown")
        tool_input = data.get("tool_input", {})

        # For now, just log — future: track file writes for richer summaries
        session = self.session_manager.get(project_name)
        if session and session.state.value == "idle":
            # Tool execution implies work is happening
            session.on_user_submit()

        self._json_response(200, {"ok": True})

    def _handle_reload(self, data: dict):
        """Reload configuration (e.g., project list changed)."""
        self._json_response(200, {"ok": True, "message": "reload not yet implemented"})

    def _resolve_project(self, data: dict) -> str:
        """Resolve a project name from hook data."""
        # Prefer explicit project name
        if data.get("project_name"):
            return data["project_name"]

        # Try to match by project path
        cwd = data.get("project_path", data.get("cwd", ""))
        if cwd and cwd in self.known_projects:
            return self.known_projects[cwd]

        # Fallback: derive from directory name
        if cwd:
            import os
            return os.path.basename(cwd.rstrip("/\\")) or "unknown"

        return data.get("session_id", "unknown")

    def _parse_body(self, body: bytes) -> dict:
        """Parse request body as JSON, or empty dict."""
        if not body:
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            # Body may be plain text (e.g., transcript snippet)
            return {"text": body.decode("utf-8", errors="replace")[:1000]}

    def _json_response(self, code: int, data: dict):
        """Send a JSON response."""
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))


class HookServer:
    """Manages the HTTP server and Claude Code file watcher lifecycle."""

    def __init__(self, config: dict):
        self.config = config
        daemon_config = config.get("daemon", {})
        self.host = daemon_config.get("host", "127.0.0.1")
        self.port = daemon_config.get("port", 9599)
        self.inactivity_timeout = daemon_config.get("inactivity_timeout", 300)
        self.httpd: Optional[HTTPServer] = None
        self._http_thread: Optional[threading.Thread] = None
        self._watch_thread: Optional[threading.Thread] = None
        self._watch_running = False

        # Wire up session manager
        self.session_manager = SessionManager(self.inactivity_timeout)

        # Build known projects map
        self.known_projects = {}
        for project in config.get("projects", []):
            if project.get("enabled", True):
                import os
                path = os.path.abspath(os.path.expanduser(project["path"]))
                self.known_projects[path] = project["name"]

    def set_notifier(self, notifier):
        """Attach a notifier for sending notifications."""
        self._notifier = notifier

    def start(self):
        """Start the HTTP server and file watcher in background threads."""
        # Inject dependencies into handler
        HookHandler.session_manager = self.session_manager
        HookHandler.notifier = getattr(self, "_notifier", None)
        HookHandler.config = self.config
        HookHandler.known_projects = self.known_projects

        # Wire up the done and permission callbacks
        self._wire_callbacks()

        # Start HTTP server
        self.httpd = HTTPServer((self.host, self.port), HookHandler)
        self._http_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self._http_thread.start()
        print(f"Hook server listening on {self.host}:{self.port}")

        # Start file watcher (for when hooks aren't available)
        self._start_watcher()
        return True

    def _start_watcher(self):
        """Start the JSONL file watcher thread."""
        from .claude_watcher import ClaudeWatcher, analyze_entries
        self._watch_running = True

        def watch_loop():
            watcher = ClaudeWatcher()
            last_activity = time.time()
            project_name = list(self.known_projects.values())[0] if self.known_projects else "default"
            session = self.session_manager.get_or_create(
                project_name,
                list(self.known_projects.keys())[0] if self.known_projects else ".",
            )
            watched_path = None
            poll_interval = 3

            while self._watch_running:
                # Find and watch the latest session file
                latest = watcher.find_latest_session()
                if latest and latest != watched_path:
                    if watched_path:
                        watcher.unwatch(watched_path)
                    watcher.watch(latest)
                    watched_path = latest
                    print(f"[watcher] Monitoring: {os.path.basename(latest)}")

                # Poll for new entries
                entries = watcher.poll()
                if entries:
                    print(f"[watcher] Got {len(entries)} new entries")
                    analysis = analyze_entries(entries)
                    last_activity = time.time()

                    if analysis["permission_needed"] and analysis["pending_tool"]:
                        tool = analysis["pending_tool"]
                        print(f"[watcher] Permission pending: {tool['name']}")
                        session.on_permission_request(tool["name"], tool["input"])
                    elif analysis["has_activity"]:
                        if session.state.value != "working":
                            session.on_user_submit()
                            session.on_stop()
                        else:
                            session.on_stop()

                # Check for inactivity → completion
                if session.state.value == "working":
                    if time.time() - last_activity > self.inactivity_timeout:
                        session.check_inactivity()

                time.sleep(poll_interval)

        self._watch_thread = threading.Thread(target=watch_loop, daemon=True)
        self._watch_thread.start()
        print(f"File watcher started (polling every 3s)")

    def _wire_callbacks(self):
        """Wire up session callbacks to the notifier."""
        notifier = getattr(self, "_notifier", None)
        if not notifier:
            return

        def on_done(project_name, project_path, duration, checkpoint_commit):
            def _send():
                print(f"\n[DONE] {project_name} — session complete ({duration})")
                summary = get_session_summary(project_path, checkpoint_commit)
                notifier.send_completion(
                    project_name=project_name,
                    duration=duration,
                    summary=summary,
                )
            threading.Thread(target=_send, daemon=True).start()

        def on_permission(project_name, tool_name, tool_input):
            def _send():
                print(f"\n[PERMISSION] {project_name} — {tool_name}")
                notifier.send_permission_request(
                    project_name=project_name,
                    tool_name=tool_name,
                    tool_input=tool_input,
                )
            threading.Thread(target=_send, daemon=True).start()

        # Attach to all sessions (existing and future)
        # We monkey-patch the session manager to auto-wire new sessions
        original_get = self.session_manager.get_or_create

        def get_or_create_with_callback(name, path):
            session = original_get(name, path)
            if not session.on_done_callback:
                session.set_done_callback(on_done)
                session.set_permission_callback(on_permission)
            return session

        self.session_manager.get_or_create = get_or_create_with_callback

    def stop(self):
        """Stop the HTTP server and file watcher."""
        self._watch_running = False
        if self._watch_thread:
            self._watch_thread.join(timeout=2)
            self._watch_thread = None
        if self.httpd:
            print("Shutting down hook server...")
            self.httpd.shutdown()
            self.httpd = None
            self._http_thread = None

    def is_running(self) -> bool:
        return self.httpd is not None and self._http_thread is not None and self._http_thread.is_alive()
