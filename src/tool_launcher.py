# -*- coding: utf-8 -*-
"""
工具启动器 - 启动AI编程工具并管理进程
"""

import os
import sys
import subprocess
import platform
import signal
import time
from typing import Dict, List, Optional, Any
from pathlib import Path


class ToolLauncher:
    """AI编程工具启动器"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.process = None
        self.project_path = None
    
    def launch_tool(self, tool_config: Dict, project_path: str) -> Optional[subprocess.Popen]:
        """
        启动AI编程工具
        
        Args:
            tool_config: 工具配置
            project_path: 项目路径
            
        Returns:
            subprocess.Popen对象或None
        """
        self.project_path = os.path.abspath(project_path)
        
        # 确保项目目录存在
        os.makedirs(self.project_path, exist_ok=True)
        
        # 获取启动命令
        command = self._build_command(tool_config)
        if not command:
            print(f"❌ 无法构建启动命令: {tool_config}")
            return None
        
        print(f"🚀 正在启动 {tool_config.get('name', '工具')}...")
        print(f"   项目路径: {self.project_path}")
        print(f"   命令: {' '.join(command)}")
        
        try:
            # 设置环境变量
            env = os.environ.copy()
            env.update(tool_config.get('env', {}))
            
            # 设置工作目录
            cwd = self.project_path
            
            # 启动进程
            if self.system == "windows":
                # Windows: 创建新控制台窗口
                creationflags = subprocess.CREATE_NEW_CONSOLE
                self.process = subprocess.Popen(
                    command,
                    cwd=cwd,
                    env=env,
                    creationflags=creationflags,
                    text=True,
                    encoding='utf-8',
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                # Unix-like: 使用pty
                self.process = subprocess.Popen(
                    command,
                    cwd=cwd,
                    env=env,
                    text=True,
                    encoding='utf-8',
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # 检查进程是否启动成功
            time.sleep(1)  # 给进程一点启动时间
            if self.process.poll() is not None:
                # 进程已经退出
                stdout, stderr = self.process.communicate()
                print(f"❌ 进程启动失败:")
                if stdout:
                    print(f"   标准输出: {stdout[:200]}")
                if stderr:
                    print(f"   错误输出: {stderr[:200]}")
                return None
            
            print(f"✅ {tool_config.get('name', '工具')} 已成功启动 (PID: {self.process.pid})")
            return self.process
            
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return None
    
    def _build_command(self, tool_config: Dict) -> List[str]:
        """构建启动命令"""
        command = tool_config.get('command', [])
        args = tool_config.get('args', [])
        
        if isinstance(command, str):
            command = [command]
        
        # 添加参数
        if args:
            if isinstance(args, str):
                command.append(args)
            elif isinstance(args, list):
                command.extend(args)
        
        return command
    
    def is_running(self) -> bool:
        """检查工具是否在运行"""
        if not self.process:
            return False
        
        return self.process.poll() is None
    
    def get_pid(self) -> Optional[int]:
        """获取进程ID"""
        if not self.process:
            return None
        
        return self.process.pid
    
    def stop(self) -> bool:
        """停止工具"""
        if not self.process:
            return True
        
        try:
            if self.system == "windows":
                # Windows: 发送Ctrl+C
                self.process.send_signal(signal.CTRL_C_EVENT)
            else:
                # Unix: 发送SIGTERM
                self.process.terminate()
            
            # 等待进程结束
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 强制终止
                self.process.kill()
                self.process.wait()
            
            print(f"✅ 工具已停止")
            return True
            
        except Exception as e:
            print(f"❌ 停止工具时出错: {e}")
            return False
    
    def wait_for_completion(self, timeout: int = None) -> bool:
        """等待工具完成"""
        if not self.process:
            return True
        
        try:
            self.process.wait(timeout=timeout)
            return True
        except subprocess.TimeoutExpired:
            return False
    
    def communicate(self, input_text: str = None) -> tuple:
        """与进程通信"""
        if not self.process:
            return ("", "")
        
        try:
            return self.process.communicate(input=input_text, timeout=1)
        except (subprocess.TimeoutExpired, ValueError):
            # 进程可能已经结束或无法通信
            return ("", "")


class ToolManager:
    """工具管理器 - 管理多个工具实例"""
    
    def __init__(self):
        self.launchers = {}  # tool_id -> ToolLauncher
        self.configs = {}    # tool_id -> config
    
    def launch(self, tool_id: str, tool_config: Dict, project_path: str) -> bool:
        """启动工具"""
        if tool_id in self.launchers:
            print(f"⚠️  工具 {tool_id} 已经在运行")
            return False
        
        launcher = ToolLauncher()
        process = launcher.launch_tool(tool_config, project_path)
        
        if process:
            self.launchers[tool_id] = launcher
            self.configs[tool_id] = tool_config
            return True
        
        return False
    
    def stop(self, tool_id: str) -> bool:
        """停止工具"""
        if tool_id not in self.launchers:
            print(f"⚠️  工具 {tool_id} 未在运行")
            return False
        
        launcher = self.launchers[tool_id]
        success = launcher.stop()
        
        if success:
            del self.launchers[tool_id]
            del self.configs[tool_id]
        
        return success
    
    def stop_all(self) -> bool:
        """停止所有工具"""
        success = True
        tool_ids = list(self.launchers.keys())
        
        for tool_id in tool_ids:
            if not self.stop(tool_id):
                success = False
        
        return success
    
    def is_running(self, tool_id: str) -> bool:
        """检查工具是否在运行"""
        if tool_id not in self.launchers:
            return False
        
        return self.launchers[tool_id].is_running()
    
    def get_running_tools(self) -> List[str]:
        """获取正在运行的工具列表"""
        running = []
        for tool_id, launcher in self.launchers.items():
            if launcher.is_running():
                running.append(tool_id)
        
        return running
    
    def get_status(self) -> Dict[str, Any]:
        """获取所有工具状态"""
        status = {}
        for tool_id, launcher in self.launchers.items():
            status[tool_id] = {
                "running": launcher.is_running(),
                "pid": launcher.get_pid(),
                "config": self.configs.get(tool_id, {})
            }
        
        return status


def create_tool_config(tool_info: Dict, approval_mode: str = "auto", aider_config: Dict = None) -> Dict:
    """创建工具配置"""
    tool_id = tool_info["id"]
    tool_name = tool_info["name"]
    
    # 基础配置
    config = {
        "name": tool_name,
        "id": tool_id,
        "command": tool_id if tool_id != "claude_code" else "claude"
    }
    
    # 添加工具特定配置
    if tool_id == "cursor":
        config.update({
            "command": "cursor",
            "args": [],
            "env": {}
        })
    elif tool_id == "aider":
        # 使用用户配置的模型
        model = "deepseek-chat"  # 默认值
        extra_args = []
        
        if aider_config:
            model = aider_config.get("model", "deepseek-chat")
            extra_args = aider_config.get("extra_args", [])
        
        args = ["--model", model]
        if extra_args:
            args.extend(extra_args)
            
        config.update({
            "command": "aider",
            "args": args,
            "env": {}
        })
    elif tool_id == "claude_code":
        config.update({
            "command": "claude",
            "args": [],
            "env": {}
        })
    elif tool_id == "codex":
        config.update({
            "command": "github-copilot",
            "args": [],
            "env": {}
        })
    elif tool_id == "tabnine":
        config.update({
            "command": "tabnine",
            "args": [],
            "env": {}
        })
    
    # 添加自动响应配置
    config["auto_response"] = {
        "enabled": approval_mode in ["auto", "smart"],
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
    
    if approval_mode == "smart":
        config["auto_response"]["blacklist"] = [
            ".*\\.env$",
            ".*secret.*",
            ".*password.*",
            ".*key.*"
        ]
    
    return config


def main():
    """测试函数"""
    print("🔧 工具启动器测试")
    print("-" * 60)
    
    # 创建测试配置
    test_config = {
        "name": "Aider",
        "id": "aider",
        "command": "python",
        "args": ["-c", "print('Hello from Aider!'); import time; time.sleep(5); print('Done!')"],
        "env": {}
    }
    
    # 启动工具
    launcher = ToolLauncher()
    project_path = os.getcwd()
    
    process = launcher.launch_tool(test_config, project_path)
    
    if process:
        print(f"\n✅ 工具已启动")
        print(f"   PID: {process.pid}")
        print(f"   等待完成...")
        
        # 等待完成
        launcher.wait_for_completion(timeout=10)
        
        print(f"\n✅ 测试完成")
    else:
        print(f"\n❌ 启动失败")


if __name__ == "__main__":
    main()