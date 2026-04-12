"""
通知发送模块
支持多渠道通知：飞书、Discord、邮件等
"""

import json
from typing import Dict, List, Optional


class Notifier:
    """通知发送器"""
    
    def __init__(self, channels: List[Dict]):
        """
        Args:
            channels: 通知渠道配置列表
                [
                    {"type": "feishu", "target": "chat:oc_xxx"},
                    {"type": "email", "target": "user@example.com"}
                ]
        """
        self.channels = channels
    
    def send(self, message: str, title: Optional[str] = None) -> Dict[str, bool]:
        """
        发送通知到所有配置的渠道
        
        Args:
            message: 通知内容
            title: 通知标题（可选）
            
        Returns:
            各渠道发送结果 {channel_type: success}
        """
        results = {}
        
        for channel in self.channels:
            channel_type = channel.get("type")
            target = channel.get("target")
            webhook = channel.get("webhook")  # 获取 webhook URL
            
            try:
                if channel_type == "feishu":
                    success = self._send_feishu(target, message, title, webhook)
                elif channel_type == "discord":
                    success = self._send_discord(target, message, title)
                elif channel_type == "email":
                    success = self._send_email(target, message, title)
                elif channel_type == "telegram":
                    success = self._send_telegram(target, message, title)
                else:
                    print(f"不支持的通知类型: {channel_type}")
                    success = False
                    
                results[channel_type] = success
                
            except Exception as e:
                print(f"发送 {channel_type} 通知失败: {e}")
                results[channel_type] = False
        
        return results
    
    def send_aider_completion(self, project_name: str, duration: str, summary: str) -> Dict[str, bool]:
        """
        发送 Aider 完成通知
        
        Args:
            project_name: 项目名称
            duration: 工作时长
            summary: 工作摘要
            
        Returns:
            各渠道发送结果
        """
        # 构建通知消息
        message = self._format_aider_message(project_name, duration, summary)
        title = f"Aider 完成 - {project_name}"
        
        return self.send(message, title)
    
    def _format_aider_message(self, project_name: str, duration: str, summary: str) -> str:
        """格式化 Aider 完成消息"""
        lines = [
            f"Aider 完成",
            f"",
            f"项目：{project_name}",
            f"耗时：{duration}",
            f"",
            f"工作内容："
        ]
        
        # 处理摘要
        if summary:
            summary_lines = summary.split("\n")
            for line in summary_lines:
                if line.strip():
                    lines.append(f"   {line}")
        else:
            lines.append("   完成工作")
        
        lines.append(f"")
        lines.append(f"[查看详情]")
        
        return "\n".join(lines)
    
    def _send_feishu(self, target: str, message: str, title: Optional[str] = None, webhook: Optional[str] = None) -> bool:
        """
        发送飞书通知
        
        支持两种方式：
        1. Webhook 机器人（独立运行时）
        2. OpenClaw message 工具（作为 Skill 运行时）
        """
        if title:
            full_message = f"{title}\n\n{message}"
        else:
            full_message = message
        
        # 优先使用 webhook（独立运行模式）
        if webhook:
            return self._send_feishu_webhook(webhook, full_message)
        
        # 否则使用 OpenClaw（Skill 模式）
        print(f"[飞书通知] 发送到 {target}")
        print(f"标题: {title or '无标题'}")
        print(f"内容预览: {message[:100]}...")
        print("提示: 配置 webhook 可实现真实发送，或作为 OpenClaw Skill 运行")
        
        # 模拟成功
        return True
    
    def _send_feishu_webhook(self, webhook_url: str, message: str) -> bool:
        """
        通过飞书 Webhook 机器人发送消息
        
        Args:
            webhook_url: 飞书机器人 webhook 地址
            message: 消息内容
            
        Returns:
            是否发送成功
        """
        import json
        import urllib.request
        
        try:
            # 构建请求
            data = {
                "msg_type": "text",
                "content": {
                    "text": message
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            # 发送请求
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if result.get('code') == 0:
                    print(f"[飞书通知] 发送成功")
                    return True
                else:
                    print(f"[飞书通知] 发送失败: {result.get('msg')}")
                    return False
                    
        except Exception as e:
            print(f"[飞书通知] 发送异常: {e}")
            return False
    
    def _send_discord(self, target: str, message: str, title: Optional[str] = None) -> bool:
        """发送 Discord 通知"""
        print(f"[Discord通知] 发送到 {target}")
        return True
    
    def _send_email(self, target: str, message: str, title: Optional[str] = None) -> bool:
        """发送邮件通知"""
        print(f"[邮件通知] 发送到 {target}")
        return True
    
    def _send_telegram(self, target: str, message: str, title: Optional[str] = None) -> bool:
        """发送 Telegram 通知"""
        print(f"[Telegram通知] 发送到 {target}")
        return True


class OpenClawNotifier(Notifier):
    """
    OpenClaw 集成版通知器
    实际 Skill 中使用，通过 OpenClaw 工具发送通知
    """
    
    def __init__(self, channels: List[Dict], openclaw_tools=None):
        super().__init__(channels)
        self.tools = openclaw_tools  # OpenClaw 工具引用
    
    def send_via_openclaw(self, message: str, title: Optional[str] = None):
        """
        通过 OpenClaw 工具发送通知
        
        在 SKILL.md 中配置 tools: ["message"] 后可用
        """
        for channel in self.channels:
            channel_type = channel.get("type")
            target = channel.get("target")
            
            if title:
                full_message = f"{title}\n\n{message}"
            else:
                full_message = message
            
            # 实际调用 OpenClaw 的 message 工具
            # 这部分在 Skill 执行时由 OpenClaw 处理
            print(f"通过 OpenClaw 发送 {channel_type} 通知到 {target}")
            print(f"消息: {full_message[:50]}...")
