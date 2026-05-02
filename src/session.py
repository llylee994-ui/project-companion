# -*- coding: utf-8 -*-
"""
Session state machine for Claude Code sentinel.
Tracks: IDLE -> WORKING -> WAITING_USER -> DONE
"""

import time
import threading
from enum import Enum
from typing import Dict, Optional, Callable


class SessionState(Enum):
    IDLE = "idle"
    WORKING = "working"
    WAITING_USER = "waiting_user"
    DONE = "done"


class Session:
    """Tracks one Claude Code session (per project)."""

    def __init__(self, project_name: str, project_path: str, inactivity_timeout: int = 300):
        self.project_name = project_name
        self.project_path = project_path
        self.inactivity_timeout = inactivity_timeout
        self.state = SessionState.IDLE
        self.last_stop_time: Optional[float] = None
        self.last_user_submit_time: Optional[float] = None
        self.session_start_time: Optional[float] = None
        self.checkpoint_commit: Optional[str] = None  # commit hash when session started
        self._timer: Optional[threading.Timer] = None
        self._done_lock = threading.Lock()
        self.on_done_callback: Optional[Callable] = None
        self.on_permission_callback: Optional[Callable] = None

    def set_done_callback(self, cb: Callable):
        self.on_done_callback = cb

    def set_permission_callback(self, cb: Callable):
        self.on_permission_callback = cb

    def record_checkpoint(self):
        """Record the current HEAD as the session checkpoint."""
        import subprocess
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                self.checkpoint_commit = result.stdout.strip()
        except Exception:
            pass

    def on_user_submit(self):
        """Called when UserPromptSubmit hook fires — user is back."""
        self.last_user_submit_time = time.time()
        self._cancel_timer()

        if self.state in (SessionState.IDLE, SessionState.DONE):
            self.state = SessionState.WORKING
            self.session_start_time = time.time()
            self.record_checkpoint()
        elif self.state == SessionState.WAITING_USER:
            self.state = SessionState.WORKING

    def on_stop(self):
        """Called when Stop hook fires — Claude finished a response."""
        self.last_stop_time = time.time()
        if self.state != SessionState.WORKING:
            return
        # Start countdown: no user activity within timeout → consider done
        self._start_done_timer()

    def on_permission_request(self, tool_name: str, tool_input: dict):
        """Called when PermissionRequest hook fires — Claude needs user approval."""
        self.last_stop_time = time.time()
        self.state = SessionState.WAITING_USER
        self._cancel_timer()

        if self.on_permission_callback:
            self.on_permission_callback(self.project_name, tool_name, tool_input)

    def _start_done_timer(self):
        """Start a timer that fires when inactivity exceeds timeout."""
        self._cancel_timer()
        self._timer = threading.Timer(self.inactivity_timeout, self._on_inactivity)
        self._timer.daemon = True
        self._timer.start()

    def _cancel_timer(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def check_inactivity(self):
        """Public method: force-check inactivity timeout. Called by file watcher."""
        self._on_inactivity()

    def _on_inactivity(self):
        """Called when inactivity timeout expires — session is done."""
        with self._done_lock:
            if self.state != SessionState.WORKING:
                return
            self.state = SessionState.DONE
        if self.on_done_callback:
            duration = ""
            if self.session_start_time:
                seconds = int(time.time() - self.session_start_time)
                if seconds < 60:
                    duration = f"{seconds}s"
                elif seconds < 3600:
                    duration = f"{seconds // 60}m {seconds % 60}s"
                else:
                    h = seconds // 3600
                    m = (seconds % 3600) // 60
                    duration = f"{h}h {m}m"
            self.on_done_callback(
                self.project_name,
                self.project_path,
                duration,
                self.checkpoint_commit,
            )

    def get_state(self) -> str:
        return self.state.value

    def get_duration(self) -> str:
        if not self.session_start_time:
            return "N/A"
        seconds = int(time.time() - self.session_start_time)
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            h = seconds // 3600
            m = (seconds % 3600) // 60
            return f"{h}h {m}m"

    def reset(self):
        self._cancel_timer()
        self.state = SessionState.IDLE
        self.last_stop_time = None
        self.last_user_submit_time = None
        self.session_start_time = None
        self.checkpoint_commit = None


class SessionManager:
    """Manages multiple project sessions."""

    def __init__(self, inactivity_timeout: int = 300):
        self.sessions: Dict[str, Session] = {}
        self.inactivity_timeout = inactivity_timeout

    def get_or_create(self, project_name: str, project_path: str) -> Session:
        if project_name not in self.sessions:
            session = Session(project_name, project_path, self.inactivity_timeout)
            self.sessions[project_name] = session
        return self.sessions[project_name]

    def get(self, project_name: str) -> Optional[Session]:
        return self.sessions.get(project_name)

    def list_sessions(self) -> list:
        return [
            {"name": s.project_name, "state": s.get_state(), "duration": s.get_duration()}
            for s in self.sessions.values()
        ]
