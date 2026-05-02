# -*- coding: utf-8 -*-
import time
from unittest.mock import patch

from src.session import Session, SessionManager, SessionState


class TestSessionStateEnum:
    def test_values(self):
        assert SessionState.IDLE.value == "idle"
        assert SessionState.WORKING.value == "working"
        assert SessionState.WAITING_USER.value == "waiting_user"
        assert SessionState.DONE.value == "done"


class TestSession:
    def test_initial_state_is_idle(self):
        s = Session("test", "/tmp/test", inactivity_timeout=10)
        assert s.get_state() == "idle"
        assert s.session_start_time is None

    def test_user_submit_transitions_to_working(self):
        s = Session("test", "/tmp/test", inactivity_timeout=10)
        s.on_user_submit()
        assert s.get_state() == "working"
        assert s.session_start_time is not None

    def test_user_submit_records_checkpoint(self):
        s = Session("test", "/tmp/test", inactivity_timeout=10)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "abc123\n"
            s.on_user_submit()
            assert s.checkpoint_commit == "abc123"

    def test_stop_starts_timer_in_working_state(self):
        s = Session("test", "/tmp/test", inactivity_timeout=1)
        s.on_user_submit()
        assert s.get_state() == "working"
        s.on_stop()
        # Timer is set but hasn't fired yet
        assert s.get_state() == "working"
        assert s._timer is not None

    def test_stop_ignored_when_not_working(self):
        s = Session("test", "/tmp/test", inactivity_timeout=1)
        s.on_stop()
        assert s.get_state() == "idle"
        assert s._timer is None

    def test_inactivity_fires_done_callback(self):
        callback_calls = []

        def cb(name, path, duration, commit):
            callback_calls.append({"name": name, "duration": duration})

        s = Session("test", "/tmp/test", inactivity_timeout=1)
        s.set_done_callback(cb)
        s.on_user_submit()
        s.on_stop()
        s._on_inactivity()
        assert s.get_state() == "done"
        assert len(callback_calls) == 1
        assert callback_calls[0]["name"] == "test"

    def test_permission_request_transitions_to_waiting(self):
        permission_calls = []

        def cb(name, tool, inp):
            permission_calls.append({"name": name, "tool": tool})

        s = Session("test", "/tmp/test", inactivity_timeout=1)
        s.set_permission_callback(cb)
        s.on_user_submit()
        s.on_permission_request("Bash", {"command": "npm test"})
        assert s.get_state() == "waiting_user"
        assert len(permission_calls) == 1
        assert permission_calls[0]["tool"] == "Bash"

    def test_resume_from_waiting(self):
        s = Session("test", "/tmp/test", inactivity_timeout=1)
        s.on_user_submit()
        s.on_permission_request("Write", {})
        assert s.get_state() == "waiting_user"
        s.on_user_submit()
        assert s.get_state() == "working"

    def test_reset(self):
        s = Session("test", "/tmp/test", inactivity_timeout=1)
        s.on_user_submit()
        s.reset()
        assert s.get_state() == "idle"
        assert s.checkpoint_commit is None
        assert s.session_start_time is None

    def test_get_duration_formatting(self):
        s = Session("test", "/tmp/test")
        s.session_start_time = time.time() - 65
        dur = s.get_duration()
        assert "1m" in dur

    def test_check_inactivity_public_method(self):
        callback_calls = []

        def cb(name, path, duration, commit):
            callback_calls.append(True)

        s = Session("test", "/tmp/test", inactivity_timeout=1)
        s.set_done_callback(cb)
        s.on_user_submit()
        s.check_inactivity()
        assert s.get_state() == "done"
        assert len(callback_calls) == 1


class TestSessionManager:
    def test_get_or_create_new_session(self):
        mgr = SessionManager()
        s = mgr.get_or_create("proj-a", "/tmp/proj-a")
        assert s.project_name == "proj-a"
        assert s.get_state() == "idle"

    def test_get_or_create_returns_same_instance(self):
        mgr = SessionManager()
        s1 = mgr.get_or_create("proj-a", "/tmp/proj-a")
        s2 = mgr.get_or_create("proj-a", "/tmp/proj-a")
        assert s1 is s2

    def test_get_nonexistent_returns_none(self):
        mgr = SessionManager()
        assert mgr.get("missing") is None

    def test_list_sessions(self):
        mgr = SessionManager()
        mgr.get_or_create("proj-a", "/tmp/a")
        mgr.get_or_create("proj-b", "/tmp/b")
        sessions = mgr.list_sessions()
        assert len(sessions) == 2
        names = {s["name"] for s in sessions}
        assert names == {"proj-a", "proj-b"}
        for s in sessions:
            assert "state" in s
            assert "duration" in s
