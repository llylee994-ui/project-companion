# -*- coding: utf-8 -*-
"""
Notification sender — Feishu / WeCom Bot / ServerChan / QQ (stub).
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

    def send_stuck_alert(
        self,
        project_name: str,
        idle_minutes: int,
    ) -> Dict[str, bool]:
        """Send a stuck-detection alert — no JSONL output for too long."""
        message = self._format_stuck(project_name, idle_minutes)
        return self._send_all(f"可能卡住 - {project_name}", message)

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

    def _format_stuck(self, project_name: str, idle_minutes: int) -> str:
        parts = [
            f"⚠️ Claude Code 可能卡住了",
            f"",
            f"📁 项目：{project_name}",
            f"⏱️ 已 {idle_minutes} 分钟没有输出",
            f"",
            f"可能原因：网络中断 / token 耗尽 / 上下文爆满 / API 超时",
            f"",
            f"💡 建议回到 Claude Code 查看状态，必要时按 Stop 重试。",
        ]
        return "\n".join(parts)

    # ---- Channel routing ----

    def _send_all(self, title: str, message: str) -> Dict[str, bool]:
        results = {}
        for channel in self.channels:
            ch_type = channel.get("type")
            try:
                if ch_type == "feishu":
                    results[ch_type] = self._send_feishu(channel, title, message)
                elif ch_type == "wecom_bot":
                    results[ch_type] = self._send_wecom_bot(channel, title, message)
                elif ch_type == "serverchan":
                    results[ch_type] = self._send_serverchan(channel, title, message)
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

    # ---- Feishu webhook ----

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
                    print(f"[feishu] 已发送")
                    self._dashboard_log("info", f"飞书已发送: {title[:30]}")
                else:
                    print(f"[feishu] 失败: {result.get('msg')}")
                    self._dashboard_log("err", f"飞书失败: {result.get('msg', '')}")
                return ok
        except Exception as e:
            print(f"[feishu] 错误: {e}")
            self._dashboard_log("err", f"飞书错误: {e}")
            return False

    # ---- 企业微信机器人 webhook ----

    def _send_wecom_bot(self, channel: Dict, title: str, message: str) -> bool:
        webhook = channel.get("webhook")
        if not webhook:
            print("[wecom_bot] No webhook configured")
            return False

        # 企业微信机器人文本消息，最大 2048 字节
        content = f"{title}\n\n{message}"
        body = {
            "msgtype": "text",
            "text": {"content": content},
        }

        try:
            req = urllib.request.Request(
                webhook,
                data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                ok = result.get("errcode") == 0
                if ok:
                    print(f"[wecom_bot] 已发送")
                    self._dashboard_log("info", f"企业微信已发送: {title[:30]}")
                else:
                    print(f"[wecom_bot] 失败: {result.get('errmsg')}")
                    self._dashboard_log("err", f"企业微信失败: {result.get('errmsg', '')}")
                return ok
        except Exception as e:
            print(f"[wecom_bot] 错误: {e}")
            self._dashboard_log("err", f"企业微信错误: {e}")
            return False

    # ---- Server酱 (个人微信) ----

    def _send_serverchan(self, channel: Dict, title: str, message: str) -> bool:
        sendkey = channel.get("sendkey")
        if not sendkey:
            print("[serverchan] No sendkey configured")
            return False

        url = f"https://sctapi.ftqq.com/{sendkey}.send"
        body = {
            "title": title,
            "desp": message.replace("\n", "\n\n"),
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                ok = result.get("code") == 0
                if ok:
                    print(f"[serverchan] 已发送")
                    self._dashboard_log("info", f"Server酱已发送: {title[:30]}")
                else:
                    print(f"[serverchan] 失败: {result.get('message')}")
                    self._dashboard_log("err", f"Server酱失败: {result.get('message', '')}")
                return ok
        except Exception as e:
            print(f"[serverchan] 错误: {e}")
            self._dashboard_log("err", f"Server酱错误: {e}")
            return False

    @staticmethod
    def _dashboard_log(level: str, text: str):
        try:
            from .hook_server import HookHandler
            HookHandler.add_log(level, text)
        except Exception:
            pass

    # ---- Stub channels (future) ----

    def _send_wechat_stub(self, channel: Dict, title: str, message: str) -> bool:
        print(f"[wechat] stub — target: {channel.get('target', 'N/A')}")
        return True

    def _send_qq_stub(self, channel: Dict, title: str, message: str) -> bool:
        print(f"[qq] stub — target: {channel.get('target', 'N/A')}")
        return True
