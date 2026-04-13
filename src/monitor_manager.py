# -*- coding: utf-8 -*-
"""
监控管理器 - 管理监控进程和配置
"""

import os
import sys
import subprocess
import threading
import time
import signal
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path


class MonitorManager:
    """监控管理器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.monitor_process = None
        self.monitor_thread = None
        self.running = False
        self.config = None
    
    def load_config(self, config: Dict = None) -> bool:
        """加载配置"""
        if config:
            self.config = config
            return True
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            print(f"✅ 已加载配置: {self.config_path}")
            return True
        except Exception as e:
            print(f"❌ 加载配置失败: {e}")
            return False
    
    def save_config(self, config: Dict = None) -> bool:
        """保存配置"""
        if config:
            self.config = config
        
        if not self.config:
            print("❌ 没有配置可保存")
            return False
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
            print(f"✅ 配置已保存到: {self.config_path}")
            return True
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
            return False
    
    def start_monitoring(self) -> bool:
        """启动监控"""
        if not self.config:
            if not self.load_config():
                return False
        
        if self.is_running():
            print("⚠️  监控已经在运行")
            return True
        
        print("🚀 启动监控进程...")
        
        try:
            # 启动监控进程
            self.monitor_process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            # 启动输出监控线程
            self.running = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_output,
                daemon=True
            )
            self.monitor_thread.start()
            
            print(f"✅ 监控已启动 (PID: {self.monitor_process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ 启动监控失败: {e}")
            return False
    
    def _monitor_output(self):
        """监控输出"""
        if not self.monitor_process:
            return
        
        while self.running and self.monitor_process:
            try:
                # 读取标准输出
                line = self.monitor_process.stdout.readline()
                if line:
                    line = line.rstrip('\n')
                    if line:  # 只打印非空行
                        print(f"[监控] {line}")
                
                # 检查进程是否结束
                if self.monitor_process.poll() is not None:
                    print("⚠️  监控进程已结束")
                    self.running = False
                    break
                    
            except Exception as e:
                # 读取错误，可能进程已结束
                break
    
    def stop_monitoring(self) -> bool:
        """停止监控"""
        if not self.is_running():
            print("⚠️  监控未在运行")
            return True
        
        print("🛑 停止监控进程...")
        self.running = False
        
        if self.monitor_process:
            try:
                # 发送中断信号
                self.monitor_process.send_signal(signal.SIGINT)
                
                # 等待进程结束
                try:
                    self.monitor_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # 强制终止
                    self.monitor_process.kill()
                    self.monitor_process.wait()
                
                print("✅ 监控已停止")
                return True
                
            except Exception as e:
                print(f"❌ 停止监控失败: {e}")
                return False
        
        return True
    
    def is_running(self) -> bool:
        """检查监控是否在运行"""
        if not self.monitor_process:
            return False
        
        return self.monitor_process.poll() is None
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        status = {
            "running": self.is_running(),
            "config_loaded": self.config is not None,
            "config_path": self.config_path
        }
        
        if self.monitor_process:
            status["pid"] = self.monitor_process.pid
            status["returncode"] = self.monitor_process.poll()
        
        return status
    
    def generate_config(self, tool_info: Dict, project_path: str, 
                       approval_mode: str = "auto", 
                       notification_enabled: bool = True,
                       aider_config: Dict = None) -> Dict:
        """生成监控配置"""
        
        # 构建项目配置
        project_config = {
            "name": f"{tool_info['name']}监控",
            "path": project_path,
            "tool": tool_info["id"],
            "enabled": True,
            "terminal_config": {
                "enabled": True,
                "auto_start": True,
                "command": self._get_tool_command(tool_info),
                "args": self._get_tool_args_with_config(tool_info, aider_config),
                "completion_markers": self._get_completion_markers(tool_info["id"]),
                "auto_response": self._get_auto_response_config(approval_mode)
            }
        }
        
        # 构建完整配置
        config = {
            "version": "2.0",
            "projects": [project_config],
            "notification": {
                "enabled": notification_enabled,
                "channels": [
                    {
                        "type": "feishu",
                        "target": "chat:oc_362047fad55744020b6c11c92951938a",
                        "webhook": "https://open.feishu.cn/open-apis/bot/v2/hook/cf13d01e-0d35-4abf-9b1e-d7af77afd6c5"
                    }
                ]
            },
            "monitoring": {
                "check_interval": 2,
                "max_session_duration": 1800
            },
            "permissions": {
                "mode": approval_mode,
                "auto_allow_patterns": [
                    ".*\\.py$",
                    ".*\\.txt$",
                    ".*\\.md$",
                    ".*test.*\\.py$",
                    ".*docs?/.*",
                    ".*config/.*"
                ]
            }
        }
        
        return config
    
    def _get_tool_command(self, tool_info: Dict) -> List[str]:
        """获取工具命令"""
        tool_id = tool_info["id"]
        
        if tool_id == "cursor":
            return ["cursor"]
        elif tool_id == "aider":
            return ["aider"]
        elif tool_id == "claude_code":
            return ["claude"]
        elif tool_id == "codex":
            return ["github-copilot"]
        elif tool_id == "tabnine":
            return ["tabnine"]
        else:
            return [tool_id]
    
    def _get_tool_args(self, tool_info: Dict) -> List[str]:
        """获取工具参数（兼容旧版本）"""
        return self._get_tool_args_with_config(tool_info, None)
    
    def _get_tool_args_with_config(self, tool_info: Dict, aider_config: Dict = None) -> List[str]:
        """获取工具参数（支持配置）"""
        tool_id = tool_info["id"]
        
        if tool_id == "aider":
            # 使用用户配置的模型
            model = "deepseek-chat"  # 默认值
            extra_args = []
            
            if aider_config:
                model = aider_config.get("model", "deepseek-chat")
                extra_args = aider_config.get("extra_args", [])
            
            args = ["--model", model]
            if extra_args:
                args.extend(extra_args)
            return args
        return []
    
    def _get_completion_markers(self, tool_id: str) -> List[str]:
        """获取完成标记"""
        base_markers = [
            "Added",
            "Committed",
            "^>",
            "✓",
            "Done",
            "Finished",
            "Completed"
        ]
        
        if tool_id == "cursor":
            base_markers.extend(["✨", "🚀", "✅"])
        elif tool_id == "claude_code":
            base_markers.extend(["Here's", "I've", "The code"])
        
        return base_markers
    
    def _get_auto_response_config(self, approval_mode: str) -> Dict:
        """获取自动响应配置"""
        if approval_mode == "auto":
            return {
                "enabled": True,
                "allow_response": "\n",  # 回车作为yes
                "deny_response": "\x03",  # Ctrl+C作为no
                "default_allow": True,
                "whitelist": [
                    ".*\\.py$",
                    ".*\\.txt$",
                    ".*\\.md$",
                    ".*\\.json$",
                    ".*\\.yaml$",
                    ".*\\.yml$"
                ]
            }
        elif approval_mode == "smart":
            return {
                "enabled": True,
                "allow_response": "\n",
                "deny_response": "\x03",
                "default_allow": True,
                "whitelist": [
                    ".*\\.py$",
                    ".*\\.txt$",
                    ".*\\.md$",
                    ".*test.*\\.py$"
                ],
                "blacklist": [
                    ".*\\.env$",
                    ".*secret.*",
                    ".*password.*",
                    ".*key.*"
                ]
            }
        else:
            return {
                "enabled": False,
                "allow_response": "y",
                "deny_response": "n",
                "default_allow": True
            }


def main():
    """测试函数"""
    print("🔧 监控管理器测试")
    print("-" * 60)
    
    manager = MonitorManager("test_config.yaml")
    
    # 生成测试配置
    test_tool = {
        "id": "aider",
        "name": "Aider",
        "description": "命令行AI编程助手"
    }
    
    config = manager.generate_config(
        test_tool,
        project_path=os.getcwd(),
        approval_mode="auto",
        notification_enabled=True
    )
    
    # 保存配置
    if manager.save_config(config):
        print("✅ 配置生成成功")
        
        # 显示配置摘要
        print("\n📋 配置摘要:")
        print(f"   项目: {config['projects'][0]['name']}")
        print(f"   工具: {config['projects'][0]['tool']}")
        print(f"   路径: {config['projects'][0]['path']}")
        print(f"   批准模式: {config['permissions']['mode']}")
        print(f"   通知: {'启用' if config['notification']['enabled'] else '禁用'}")
    
    # 测试状态
    status = manager.get_status()
    print(f"\n📊 监控状态: {'运行中' if status['running'] else '未运行'}")


if __name__ == "__main__":
    main()