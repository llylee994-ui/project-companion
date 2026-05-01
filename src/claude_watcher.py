# -*- coding: utf-8 -*-
"""
Claude Code session file watcher — multi-session support.
Monitors ~/.claude/projects/*/session.jsonl files for new activity.
"""

import os
import json
import time
import threading
import glob
from typing import Optional


class ClaudeWatcher:
    """Watches multiple Claude Code session JSONL files for new entries."""

    def __init__(self, claude_home: Optional[str] = None):
        self.claude_home = claude_home or os.path.expanduser("~/.claude")
        self.projects_dir = os.path.join(self.claude_home, "projects")
        self._watched: dict = {}  # path -> {"pos": int, "mtime": float, "session_id": str}
        self._lock = threading.Lock()

    def find_active_sessions(self, within_seconds: int = 600) -> list:
        """
        Find all recently active session files.
        Returns list of (path, session_id) sorted by mtime desc.
        """
        now = time.time()
        results = []
        pattern = os.path.join(self.projects_dir, "*", "*.jsonl")
        for f in glob.glob(pattern):
            if "subagents" in f:
                continue
            try:
                mtime = os.path.getmtime(f)
                if now - mtime < within_seconds:
                    sid = os.path.splitext(os.path.basename(f))[0]
                    results.append((mtime, f, sid))
            except OSError:
                pass
        results.sort(reverse=True)
        return [(path, sid) for _, path, sid in results]

    def ensure_watching(self, session_path: str, session_id: str):
        """Add a session to the watch list if not already watched."""
        with self._lock:
            if session_path not in self._watched:
                try:
                    size = os.path.getsize(session_path)
                    self._watched[session_path] = {
                        "pos": size,
                        "mtime": os.path.getmtime(session_path),
                        "session_id": session_id,
                    }
                except OSError:
                    pass

    def remove_stale(self, within_seconds: int = 900):
        """Remove sessions that haven't been modified recently."""
        now = time.time()
        with self._lock:
            stale = []
            for path, state in self._watched.items():
                try:
                    if now - os.path.getmtime(path) > within_seconds:
                        stale.append(path)
                except OSError:
                    stale.append(path)
            for path in stale:
                del self._watched[path]

    def poll(self) -> dict:
        """
        Poll all watched files for new lines.
        Returns {session_path: [(entries, session_id)]}
        """
        results = {}
        with self._lock:
            for path, state in list(self._watched.items()):
                try:
                    if not os.path.exists(path):
                        del self._watched[path]
                        continue
                    current_mtime = os.path.getmtime(path)
                    current_size = os.path.getsize(path)
                    if current_mtime == state["mtime"] and current_size == state["pos"]:
                        continue
                    if current_size < state["pos"]:
                        state["pos"] = 0
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        f.seek(state["pos"])
                        new_data = f.read()
                        state["pos"] = f.tell()
                        state["mtime"] = current_mtime
                    entries = []
                    for line in new_data.strip().split("\n"):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
                    if entries:
                        results[path] = (entries, state["session_id"])
                except OSError:
                    pass
        return results


def analyze_entries(entries: list) -> dict:
    """
    Analyze polled JSONL entries.
    Detects tool_use blocks inside assistant.message.content.
    """
    result = {
        "permission_needed": False,
        "pending_tool": None,
        "has_activity": False,
    }
    for entry in entries:
        result["has_activity"] = True
        t = entry.get("type", "")
        if t == "assistant":
            msg = entry.get("message", {})
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        result["permission_needed"] = True
                        result["pending_tool"] = {
                            "name": block.get("name", "unknown"),
                            "input": block.get("input", {}),
                        }
                        return result
    return result
