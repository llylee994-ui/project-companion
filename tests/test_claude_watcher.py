# -*- coding: utf-8 -*-
import json
import os
import tempfile

import pytest

from src.claude_watcher import analyze_entries, ClaudeWatcher


class TestAnalyzeEntries:
    """Tests for the core tool-detection logic."""

    def test_no_entries_means_no_activity(self):
        result = analyze_entries([])
        assert result["has_activity"] is False
        assert result["permission_needed"] is False
        assert result["pending_tool"] is None

    def test_detects_permission_tool_bash(self):
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Bash",
                            "input": {"command": "npm install"},
                        }
                    ]
                },
            }
        ]
        result = analyze_entries(entries)
        assert result["has_activity"] is True
        assert result["permission_needed"] is True
        assert result["pending_tool"]["name"] == "Bash"
        assert result["pending_tool"]["input"]["command"] == "npm install"

    def test_detects_write_as_permission(self):
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Write", "input": {"file_path": "/tmp/x"}}
                    ]
                },
            }
        ]
        result = analyze_entries(entries)
        assert result["permission_needed"] is True
        assert result["pending_tool"]["name"] == "Write"

    def test_read_is_auto_tool_no_permission(self):
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Read", "input": {"file_path": "x.py"}}
                    ]
                },
            }
        ]
        result = analyze_entries(entries)
        assert result["has_activity"] is True
        assert result["permission_needed"] is False
        assert result["pending_tool"] is None

    def test_grep_is_auto_tool(self):
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Grep", "input": {"pattern": "foo"}}
                    ]
                },
            }
        ]
        result = analyze_entries(entries)
        assert result["permission_needed"] is False

    def test_glob_is_auto_tool(self):
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Glob", "input": {"pattern": "*.py"}}
                    ]
                },
            }
        ]
        result = analyze_entries(entries)
        assert result["permission_needed"] is False

    def test_unknown_tool_is_conservative(self):
        """Unknown tools are treated as needing permission (safety)."""
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "NewMagicTool", "input": {}}
                    ]
                },
            }
        ]
        result = analyze_entries(entries)
        assert result["permission_needed"] is True
        assert result["pending_tool"]["name"] == "NewMagicTool"

    def test_returns_first_permission_tool_only(self):
        """When multiple tools exist, returns the first permission-needed one."""
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Glob", "input": {}},
                        {"type": "tool_use", "name": "Bash", "input": {"command": "rm -rf /"}},
                        {"type": "tool_use", "name": "Write", "input": {}},
                    ]
                },
            }
        ]
        result = analyze_entries(entries)
        assert result["pending_tool"]["name"] == "Bash"

    def test_non_assistant_entry(self):
        entries = [{"type": "user", "message": {"content": [{"type": "text", "text": "hi"}]}}]
        result = analyze_entries(entries)
        assert result["permission_needed"] is False

    def test_content_not_a_list(self):
        entries = [{"type": "assistant", "message": {"content": "plain string"}}]
        result = analyze_entries(entries)
        assert result["permission_needed"] is False

    def test_detects_tool_result_in_user_entry(self):
        entries = [
            {
                "type": "user",
                "message": {
                    "content": [
                        {"type": "tool_result", "tool_use_id": "toolu_abc123"}
                    ]
                },
            }
        ]
        result = analyze_entries(entries)
        assert result["has_activity"] is True
        assert "toolu_abc123" in result["tool_results"]

    def test_tool_result_not_in_assistant_entry(self):
        """tool_result only lives inside user entries, not assistant."""
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_result", "tool_use_id": "toolu_xyz"}
                    ]
                },
            }
        ]
        result = analyze_entries(entries)
        assert result["tool_results"] == set()

    def test_auto_approve_scenario_same_batch(self):
        """Permission tool + tool_result in same batch → auto-approved."""
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Write", "input": {}}
                    ]
                },
            },
            {
                "type": "user",
                "message": {
                    "content": [
                        {"type": "tool_result", "tool_use_id": "toolu_001"}
                    ]
                },
            },
        ]
        result = analyze_entries(entries)
        assert result["permission_needed"] is True
        assert result["pending_tool"]["name"] == "Write"
        assert len(result["tool_results"]) > 0  # caller sees both → auto-approved

    def test_permission_without_tool_result(self):
        """Permission tool but no tool_result → needs deferral."""
        entries = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Write", "input": {}}
                    ]
                },
            }
        ]
        result = analyze_entries(entries)
        assert result["permission_needed"] is True
        assert result["tool_results"] == set()  # caller should defer


class TestClaudeWatcherGetProjectName:
    def test_reads_cwd_from_jsonl(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"cwd": "/home/user/my-project"}, f)
            f.write("\n")
            f.flush()
            watcher = ClaudeWatcher()
            name, cwd = watcher.get_project_name(f.name)
        os.unlink(f.name)
        assert name == "my-project"
        assert cwd == "/home/user/my-project"

    def test_fallback_when_no_cwd(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"type": "user"}, f)
            f.write("\n")
            f.flush()
            watcher = ClaudeWatcher()
            name, cwd = watcher.get_project_name(f.name)
        os.unlink(f.name)
        assert isinstance(name, str)
        assert cwd == ""

    def test_empty_file_fallback(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            f.flush()
            watcher = ClaudeWatcher()
            name, cwd = watcher.get_project_name(f.name)
        os.unlink(f.name)
        assert isinstance(name, str)
        assert cwd == ""
