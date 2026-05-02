# -*- coding: utf-8 -*-
import os
import tempfile
from pathlib import Path

import pytest

from src.utils import expand_path, format_duration, truncate_string, load_config


class TestFormatDuration:
    def test_seconds(self):
        assert format_duration(0) == "0秒"
        assert format_duration(30) == "30秒"
        assert format_duration(59) == "59秒"

    def test_minutes(self):
        assert format_duration(60) == "1分钟"
        assert format_duration(1800) == "30分钟"
        assert format_duration(3599) == "59分钟"

    def test_hours(self):
        assert format_duration(3600) == "1小时"
        assert format_duration(7200) == "2小时"

    def test_hours_and_minutes(self):
        assert format_duration(3660) == "1小时1分钟"
        assert format_duration(5400) == "1小时30分钟"


class TestTruncateString:
    def test_short_string_passes_through(self):
        assert truncate_string("hello", max_length=10) == "hello"

    def test_exact_length_passes_through(self):
        assert truncate_string("1234567890", max_length=10) == "1234567890"

    def test_truncates_with_default_suffix(self):
        assert truncate_string("a" * 200, max_length=10) == "aaaaaaa..."

    def test_custom_max_and_suffix(self):
        result = truncate_string("hello world", max_length=8, suffix="..")
        assert result == "hello .."
        assert len(result) == 8


class TestExpandPath:
    def test_expands_tilde(self):
        result = expand_path("~/Documents")
        assert not result.startswith("~")
        assert result.endswith("Documents")

    def test_abspath(self):
        result = expand_path("/foo/bar")
        assert os.path.isabs(result)

    def test_relative_path(self):
        result = expand_path("foo/bar")
        assert os.path.isabs(result)


class TestLoadConfig:
    def test_loads_valid_yaml(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write("version: '1.0'\nname: test\n")
            f.flush()
            result = load_config(f.name)
        os.unlink(f.name)
        assert result == {"version": "1.0", "name": "test"}

    def test_returns_none_for_missing_file(self):
        result = load_config("/nonexistent/path/config.yaml")
        assert result is None

    def test_returns_none_for_invalid_yaml(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(": invalid yaml :::\n")
            f.flush()
            result = load_config(f.name)
        os.unlink(f.name)
        assert result is None
