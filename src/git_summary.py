# -*- coding: utf-8 -*-
"""
Git-based change summary — zero LLM tokens.
Runs git diff/log to produce a concise summary of what changed.
"""

import subprocess
import os
from typing import Dict, Optional


def run_git(args: list, cwd: str) -> Optional[str]:
    """Run a git command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except Exception:
        return None


def get_diff_stat(project_path: str, base_ref: str = "HEAD") -> Dict:
    """
    Get diff statistics for the working tree vs base_ref.
    Returns {files_changed, insertions, deletions, file_list}
    """
    stat = run_git(["diff", "--stat", base_ref], project_path)
    if not stat:
        return {"files_changed": 0, "insertions": 0, "deletions": 0, "file_list": []}

    # Parse the last line: "N files changed, X insertions(+), Y deletions(-)"
    lines = stat.strip().split("\n")
    summary = lines[-1] if lines else ""
    files_changed = 0
    insertions = 0
    deletions = 0

    import re

    m = re.search(r"(\d+)\s+files?\s+changed", summary)
    if m:
        files_changed = int(m.group(1))
    m = re.search(r"(\d+)\s+insertions?\(\+\)", summary)
    if m:
        insertions = int(m.group(1))
    m = re.search(r"(\d+)\s+deletions?\(-\)", summary)
    if m:
        deletions = int(m.group(1))

    # Build file list from the stat lines
    file_list = []
    for line in lines[:-1]:
        # Format: "path/to/file | 12 ++++++++-------"
        parts = line.split("|")
        if parts:
            name = parts[0].strip()
            if name:
                file_list.append(name)

    return {
        "files_changed": files_changed,
        "insertions": insertions,
        "deletions": deletions,
        "file_list": file_list,
    }


def get_recent_commits(project_path: str, count: int = 5) -> list:
    """Get the last N commits as {hash, subject, author} dicts."""
    output = run_git(
        ["log", f"-{count}", "--format=%h||%s||%an"], project_path
    )
    if not output:
        return []

    commits = []
    for line in output.strip().split("\n"):
        parts = line.split("||", 2)
        if len(parts) == 3:
            commits.append(
                {"hash": parts[0], "subject": parts[1], "author": parts[2]}
            )
    return commits


def get_uncommitted_summary(project_path: str) -> str:
    """Generate a summary of uncommitted changes (for task-in-progress)."""
    stat = get_diff_stat(project_path)

    if stat["files_changed"] == 0:
        return "(no changes detected)"

    lines = [
        f"{stat['files_changed']} files changed",
        f"+{stat['insertions']} -{stat['deletions']}",
    ]

    if stat["file_list"]:
        shown = stat["file_list"][:5]
        for f in shown:
            lines.append(f"  - {f}")
        if len(stat["file_list"]) > 5:
            lines.append(f"  ... and {len(stat['file_list']) - 5} more")

    return "\n".join(lines)


def get_session_summary(project_path: str, start_ref: Optional[str] = None) -> str:
    """
    Generate a complete session summary.
    Uses uncommitted diff + recent commits since start_ref.

    Returns a formatted string ready for Feishu notification.
    """
    stat = get_diff_stat(project_path)

    if start_ref:
        stat = get_diff_stat(project_path, start_ref)

    recent_commits = get_recent_commits(project_path, 5)

    lines = [
        "AI Coding Companion - 工作摘要",
        "",
    ]

    # Code statistics
    if stat["files_changed"] > 0:
        lines.append(f"Files: {stat['files_changed']}")
        lines.append(f"Lines: +{stat['insertions']} -{stat['deletions']}")
        if stat["file_list"]:
            shown = stat["file_list"][:5]
            lines.append("")
            lines.append("Changed files:")
            for f in shown:
                lines.append(f"  {f}")
            if len(stat["file_list"]) > 5:
                lines.append(f"  ... and {len(stat['file_list']) - 5} more")
    else:
        lines.append("Files: 0 changed")

    # Recent commits
    if recent_commits:
        lines.append("")
        lines.append("Recent commits:")
        for c in recent_commits[:3]:
            lines.append(f"  {c['hash']} {c['subject']} ({c['author']})")

    return "\n".join(lines)
