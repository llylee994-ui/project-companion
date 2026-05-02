# -*- coding: utf-8 -*-
from src.notifier import Notifier


class TestFormatCompletion:
    def test_contains_project_name_and_duration(self):
        n = Notifier([])
        msg = n._format_completion("my-project", "30m 5s", "完成了重构")
        assert "my-project" in msg
        assert "30m 5s" in msg
        assert "完成了重构" in msg

    def test_empty_summary_fallback(self):
        n = Notifier([])
        msg = n._format_completion("test", "1h", "")
        assert "任务已完成" in msg or "test" in msg


class TestFormatPermission:
    def test_contains_project_and_tool(self):
        n = Notifier([])
        msg = n._format_permission("proj-x", "Bash", {"command": "git push"})
        assert "proj-x" in msg
        assert "执行命令" in msg

    def test_shows_first_key_param(self):
        n = Notifier([])
        msg = n._format_permission("proj", "Write", {"file_path": "/tmp/out.txt"})
        assert "file_path" in msg
        assert "/tmp/out.txt" in msg

    def test_unknown_tool_shows_raw_name(self):
        n = Notifier([])
        msg = n._format_permission("proj", "SomeNewTool", {})
        assert "SomeNewTool" in msg

    def test_empty_input_does_not_crash(self):
        n = Notifier([])
        msg = n._format_permission("proj", "Bash", {})
        assert "proj" in msg
        assert "执行命令" in msg


class TestFormatStuck:
    def test_contains_project_and_minutes(self):
        n = Notifier([])
        msg = n._format_stuck("my-app", 30)
        assert "my-app" in msg
        assert "30" in msg

    def test_suggests_checking_status(self):
        n = Notifier([])
        msg = n._format_stuck("x", 5)
        assert "Claude Code" in msg or "卡住" in msg


class TestSendAll:
    def test_unknown_channel_type_returns_false(self):
        n = Notifier([{"type": "carrier_pigeon"}])
        results = n._send_all("title", "message")
        assert "carrier_pigeon" in results
        assert results["carrier_pigeon"] is False

    def test_empty_channels_returns_empty_dict(self):
        n = Notifier([])
        results = n._send_all("title", "message")
        assert results == {}
