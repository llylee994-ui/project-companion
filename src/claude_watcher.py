# -*- coding: utf-8 -*-
"""
Claude Code session file watcher.
Monitors ~/.claude/projects/*/session.jsonl files for new activity.
Replaces hook-based monitoring when hooks aren't available.
"""

import os
import json
import time
import threading
import glob
from typing import Optional, Callable


class ClaudeWatcher:
    """Watches Claude Code session JSONL files for new entries."""

    def __init__(self, claude_home: Optional[str] = None):
        self.claude_home = claude_home or os.path.expanduser("~/.claude")
        self.projects_dir = os.path.join(self.claude_home, "projects")
        self._watched_files: dict = {}  # session_id -> {"path": ..., "pos": ..., "mtime": ...}
        self._lock = threading.Lock()

    def find_latest_session(self, project_path: str = None) -> Optional[str]:
        """Find the most recently modified session JSONL file."""
        latest_path = None
        latest_mtime = 0

        pattern = os.path.join(self.projects_dir, "*", "*.jsonl")
        for f in glob.glob(pattern):
            # Skip subagent sessions
            if "subagents" in f:
                continue
            try:
                mtime = os.path.getmtime(f)
                if mtime > latest_mtime:
                    latest_mtime = mtime
                    latest_path = f
            except OSError:
                pass

        return latest_path

    def watch(self, session_path: str):
        """Start watching a session file from its current end."""
        with self._lock:
            try:
                size = os.path.getsize(session_path)
                self._watched_files[session_path] = {
                    "pos": size,
                    "mtime": os.path.getmtime(session_path),
                }
            except OSError:
                pass

    def poll(self) -> list:
        """
        Poll watched files for new lines.
        Returns list of parsed JSON entries.
        """
        entries = []
        with self._lock:
            for path, state in list(self._watched_files.items()):
                try:
                    if not os.path.exists(path):
                        continue
                    current_mtime = os.path.getmtime(path)
                    current_size = os.path.getsize(path)

                    if current_mtime == state["mtime"] and current_size == state["pos"]:
                        continue  # No changes

                    if current_size < state["pos"]:
                        # File was truncated — reset
                        state["pos"] = 0

                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        f.seek(state["pos"])
                        new_data = f.read()
                        state["pos"] = f.tell()
                        state["mtime"] = current_mtime

                    for line in new_data.strip().split("\n"):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                            entries.append(entry)
                        except json.JSONDecodeError:
                            pass
                except OSError:
                    pass
        return entries

    def unwatch(self, session_path: str):
        with self._lock:
            self._watched_files.pop(session_path, None)


def analyze_entries(entries: list) -> dict:
    """
    Analyze polled JSONL entries.
    Returns {"permission_needed": bool, "last_assistant_text": str, "has_activity": bool}
    """
    result = {
        "permission_needed": False,
        "last_assistant_text": "",
        "has_activity": False,
        "tool_calls": [],
    }

    for entry in entries:
        result["has_activity"] = True
        t = entry.get("type", "")

        if t == "assistant":
            content = entry.get("content", [])
            if content and isinstance(content, list):
                for block in content:
                    text = block.get("text", "")
                    if text:
                        result["last_assistant_text"] = text
                        if _has_permission_pattern(text):
                            result["permission_needed"] = True

        elif t == "tool_use":
            result["tool_calls"].append({
                "name": entry.get("name", "unknown"),
                "input": entry.get("input", {}),
            })

    return result


PERMISSION_PATTERNS = [
    "Do you want to proceed?",
    "Shall I",
    "Are you sure",
    "Permission",
    "Allow",
    "Deny",
    "Proceed?",
    "Continue?",
    "(y/n)",
    "[y/n]",
    "(yes/no)",
    "[yes/no]",
    "需要你",
    "是否",
    "确认",
    "允许",
]


def _has_permission_pattern(text: str) -> bool:
    text_lower = text.lower()
    for p in PERMISSION_PATTERNS:
        if p.lower() in text_lower:
            return True
    return False
