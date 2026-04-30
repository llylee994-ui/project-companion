# -*- coding: utf-8 -*-
"""
Notification sender — Feishu webhook (real), WeChat/QQ (stubs).
"""

import json
import urllib.request
from typing import Dict, List, Optional


class Notifier:
    """Multi-channel notification sender."""

    def __init__(self, channels: List[Dict]):
        self.channels = channels

    def send_completion(
        self,
        project_name: str,
        duration: str,
        summary: str,
    ) -> Dict[str, bool]:
        """Send a completion notification."""
        message = self._format_completion(project_name, duration, summary)
        return self._send_all(f"任务完成 - {project_name}", message)

    def send_permission_request(
        self,
        project_name: str,
        tool_name: str = "",
        tool_input: dict = None,
    ) -> Dict[str, bool]:
        """Send a permission-request notification (triggered by PermissionRequest hook)."""
        message = self._format_permission(project_name, tool_name, tool_input or {})
        return self._send_all(f"需要确认 - {project_name}", message)

    # ---- Formatting ----

    def _format_completion(self, project_name: str, duration: str, summary: str) -> str:
        parts = [
            f"🎉 AI 编程伴侣",
            f"",
            f"📁 项目：{project_name}",
            f"⏱️ 耗时：{duration}",
            f"",
            summary if summary else "任务已完成。",
            f"",
            f"可以回来看看了~",
        ]
        return "\n".join(parts)

    def _format_permission(self, project_name: str, tool_name: str, tool_input: dict) -> str:
        # 翻译常见工具名为中文
        TOOL_NAMES = {
            "Bash": "执行命令",
            "Read": "读取文件",
            "Write": "写入文件",
            "Edit": "编辑文件",
            "Glob": "搜索文件",
            "Grep": "搜索内容",
            "WebFetch": "访问网页",
            "WebSearch": "网络搜索",
            "Task": "子任务",
        }
        tool_label = TOOL_NAMES.get(tool_name, tool_name)

        parts = [
            f"🔐 Claude Code 需要你的确认",
            f"",
            f"📁 项目：{project_name}",
            f"🔧 操作：{tool_label}",
        ]

        # 显示关键参数（如文件路径、命令等）
        if tool_input:
            for key in ("command", "file_path", "url", "pattern", "query", "description"):
                val = tool_input.get(key, "")
                if val:
                    val_str = str(val)[:150]
                    parts.append(f"   {key}: {val_str}")
                    break  # 只显示第一个关键参数

        parts.append("")
        parts.append("💡 请回到 Claude Code 点击 Allow / Deny。")
        return "\n".join(parts)

    # ---- Channel routing ----

    def _send_all(self, title: str, message: str) -> Dict[str, bool]:
        results = {}
        for channel in self.channels:
            ch_type = channel.get("type")
            try:
                if ch_type == "feishu":
                    results[ch_type] = self._send_feishu(channel, title, message)
                elif ch_type == "wechat":
                    results[ch_type] = self._send_wechat_stub(channel, title, message)
                elif ch_type == "qq":
                    results[ch_type] = self._send_qq_stub(channel, title, message)
                else:
                    results[ch_type] = False
            except Exception as e:
                print(f"[notifier] {ch_type} error: {e}")
                results[ch_type] = False
        return results

    # ---- Feishu webhook (real) ----

    def _send_feishu(self, channel: Dict, title: str, message: str) -> bool:
        webhook = channel.get("webhook")
        if not webhook:
            print("[feishu] No webhook configured")
            return False

        body = {
            "msg_type": "text",
            "content": {"text": f"{title}\n\n{message}"},
        }

        try:
            req = urllib.request.Request(
                webhook,
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                ok = result.get("code") == 0
                if ok:
                    print(f"[feishu] Sent successfully")
                else:
                    print(f"[feishu] Failed: {result.get('msg')}")
                return ok
        except Exception as e:
            print(f"[feishu] Error: {e}")
            return False

    # ---- Stub channels (future) ----

    def _send_wechat_stub(self, channel: Dict, title: str, message: str) -> bool:
        print(f"[wechat] stub — target: {channel.get('target', 'N/A')}")
        return True

    def _send_qq_stub(self, channel: Dict, title: str, message: str) -> bool:
        print(f"[qq] stub — target: {channel.get('target', 'N/A')}")
        return True
