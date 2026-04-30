# -*- coding: utf-8 -*-
"""
AI编程工具检测器 — 检测 Claude Code 安装状态。
骨架保留，后续可扩展其他工具。
"""

import os
import subprocess
import platform
from typing import Dict, List, Optional


class ToolDetector:
    """AI编程工具检测器"""

    def __init__(self):
        self.system = platform.system().lower()

    def detect_installed_tools(self) -> List[Dict]:
        """检测已安装的 AI 编程工具"""
        tools = []

        claude = self._detect_claude()
        if claude:
            tools.append(claude)

        # 后续可在此添加其他工具检测 (Cursor, Aider, Codex...)

        return tools

    def _detect_claude(self) -> Optional[Dict]:
        """检测 Claude Code"""
        info = {
            "id": "claude_code",
            "name": "Claude Code",
            "description": "Anthropic 的 Claude 编程工具",
            "command_found": False,
            "install_path_found": False,
            "executable_found": False,
        }

        # 1. 命令检测 (where/which claude)
        try:
            if self.system == "windows":
                result = subprocess.run(
                    ["where", "claude"], capture_output=True, text=True, timeout=2
                )
            else:
                result = subprocess.run(
                    ["which", "claude"], capture_output=True, text=True, timeout=2
                )
            if result.returncode == 0 and result.stdout.strip():
                info["command_found"] = True
                info["command_path"] = result.stdout.strip().split("\n")[0]
        except Exception:
            pass

        # 2. 路径检测
        if self.system == "windows":
            paths = [
                os.path.expanduser("~/AppData/Local/Claude/Claude.exe"),
                "C:/Program Files/Claude/Claude.exe",
            ]
        elif self.system == "darwin":
            paths = [
                "/Applications/Claude.app",
                os.path.expanduser("~/Applications/Claude.app"),
            ]
        else:
            paths = [
                "/usr/bin/claude",
                os.path.expanduser("~/.local/bin/claude"),
            ]

        for p in paths:
            if os.path.exists(p):
                info["executable_found"] = True
                info["executable_path"] = p
                info["install_path_found"] = True
                info["install_path"] = os.path.dirname(p)
                break

        if any([info["command_found"], info["install_path_found"], info["executable_found"]]):
            return info
        return None


def main():
    """测试"""
    detector = ToolDetector()
    tools = detector.detect_installed_tools()
    if tools:
        for t in tools:
            print(f"{t['name']}: {'可用' if t['command_found'] or t['executable_found'] else '未检测到'}")
    else:
        print("未检测到任何 AI 编程工具")


if __name__ == "__main__":
    main()
