# -*- coding: utf-8 -*-
"""
工具检测器 - 检测电脑中安装的AI编程工具
"""

import os
import sys
import subprocess
import platform
from typing import Dict, List, Optional


class ToolDetector:
    """AI编程工具检测器"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.tools = self._get_tool_definitions()
    
    def _get_tool_definitions(self) -> List[Dict]:
        """获取工具定义"""
        return [
            {
                "id": "cursor",
                "name": "Cursor",
                "description": "AI驱动的代码编辑器",
                "detection_methods": [
                    self._detect_cursor_windows,
                    self._detect_cursor_mac,
                    self._detect_cursor_linux,
                    self._detect_by_command
                ]
            },
            {
                "id": "aider",
                "name": "Aider",
                "description": "命令行AI编程助手",
                "detection_methods": [
                    self._detect_by_command,
                    self._detect_python_package
                ]
            },
            {
                "id": "claude_code",
                "name": "Claude Code",
                "description": "Anthropic的Claude编程工具",
                "detection_methods": [
                    self._detect_by_command,
                    self._detect_claude_app
                ]
            },
            {
                "id": "codex",
                "name": "Codex",
                "description": "GitHub Copilot CLI",
                "detection_methods": [
                    self._detect_by_command,
                    self._detect_github_copilot
                ]
            },
            {
                "id": "tabnine",
                "name": "Tabnine",
                "description": "AI代码补全工具",
                "detection_methods": [
                    self._detect_by_command,
                    self._detect_tabnine_app
                ]
            }
        ]
    
    def detect_installed_tools(self) -> List[Dict]:
        """检测已安装的工具"""
        detected_tools = []
        
        for tool_def in self.tools:
            tool_info = self._detect_tool(tool_def)
            if tool_info:
                detected_tools.append(tool_info)
        
        return detected_tools
    
    def _detect_tool(self, tool_def: Dict) -> Optional[Dict]:
        """检测单个工具"""
        tool_id = tool_def["id"]
        tool_name = tool_def["name"]
        
        # 基础工具信息
        tool_info = {
            "id": tool_id,
            "name": tool_name,
            "description": tool_def["description"],
            "command_found": False,
            "install_path_found": False,
            "executable_found": False,
            "command_path": None,
            "install_path": None,
            "executable_path": None
        }
        
        # 尝试所有检测方法
        for detection_method in tool_def["detection_methods"]:
            try:
                result = detection_method(tool_id, tool_name)
                if result:
                    tool_info.update(result)
                    break
            except Exception as e:
                # 检测方法失败，继续尝试下一个
                continue
        
        # 如果任何检测方法成功，返回工具信息
        if any([tool_info['command_found'], tool_info['install_path_found'], tool_info['executable_found']]):
            return tool_info
        
        return None
    
    def _detect_by_command(self, tool_id: str, tool_name: str) -> Optional[Dict]:
        """通过命令检测工具"""
        # 尝试运行工具命令
        command = tool_id if tool_id != "claude_code" else "claude"
        
        try:
            if self.system == "windows":
                result = subprocess.run(
                    ["where", command],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
            else:
                result = subprocess.run(
                    ["which", command],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
            
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip().split('\n')[0]
                return {
                    "command_found": True,
                    "command_path": path
                }
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        return None
    
    def _detect_cursor_windows(self, tool_id: str, tool_name: str) -> Optional[Dict]:
        """在Windows上检测Cursor"""
        if self.system != "windows":
            return None
        
        # 检查常见安装路径
        possible_paths = [
            os.path.expanduser("~/AppData/Local/Programs/Cursor/Cursor.exe"),
            os.path.expanduser("~/AppData/Local/Cursor/Cursor.exe"),
            "C:/Program Files/Cursor/Cursor.exe",
            "C:/Program Files (x86)/Cursor/Cursor.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return {
                    "executable_found": True,
                    "executable_path": path,
                    "install_path_found": True,
                    "install_path": os.path.dirname(path)
                }
        
        return None
    
    def _detect_cursor_mac(self, tool_id: str, tool_name: str) -> Optional[Dict]:
        """在macOS上检测Cursor"""
        if self.system != "darwin":
            return None
        
        # 检查常见安装路径
        possible_paths = [
            "/Applications/Cursor.app",
            os.path.expanduser("~/Applications/Cursor.app")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return {
                    "executable_found": True,
                    "executable_path": path,
                    "install_path_found": True,
                    "install_path": path
                }
        
        return None
    
    def _detect_cursor_linux(self, tool_id: str, tool_name: str) -> Optional[Dict]:
        """在Linux上检测Cursor"""
        if self.system != "linux":
            return None
        
        # 检查常见安装路径
        possible_paths = [
            "/usr/bin/cursor",
            "/usr/local/bin/cursor",
            os.path.expanduser("~/.local/bin/cursor"),
            os.path.expanduser("~/cursor/cursor")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return {
                    "executable_found": True,
                    "executable_path": path,
                    "install_path_found": True,
                    "install_path": os.path.dirname(path)
                }
        
        return None
    
    def _detect_python_package(self, tool_id: str, tool_name: str) -> Optional[Dict]:
        """检测Python包"""
        if tool_id != "aider":
            return None
        
        try:
            # 尝试导入aider包
            import importlib.util
            spec = importlib.util.find_spec("aider")
            if spec and spec.origin:
                return {
                    "install_path_found": True,
                    "install_path": os.path.dirname(spec.origin)
                }
        except ImportError:
            pass
        
        return None
    
    def _detect_claude_app(self, tool_id: str, tool_name: str) -> Optional[Dict]:
        """检测Claude应用"""
        if tool_id != "claude_code":
            return None
        
        if self.system == "windows":
            paths = [
                os.path.expanduser("~/AppData/Local/Claude/Claude.exe"),
                "C:/Program Files/Claude/Claude.exe"
            ]
        elif self.system == "darwin":
            paths = [
                "/Applications/Claude.app",
                os.path.expanduser("~/Applications/Claude.app")
            ]
        else:
            paths = [
                "/usr/bin/claude",
                os.path.expanduser("~/.local/bin/claude")
            ]
        
        for path in paths:
            if os.path.exists(path):
                return {
                    "executable_found": True,
                    "executable_path": path,
                    "install_path_found": True,
                    "install_path": os.path.dirname(path)
                }
        
        return None
    
    def _detect_github_copilot(self, tool_id: str, tool_name: str) -> Optional[Dict]:
        """检测GitHub Copilot"""
        if tool_id != "codex":
            return None
        
        # GitHub Copilot通常作为VS Code扩展安装
        # 检查VS Code扩展目录
        if self.system == "windows":
            vscode_ext_path = os.path.expanduser("~/.vscode/extensions")
        elif self.system == "darwin":
            vscode_ext_path = os.path.expanduser("~/Library/Application Support/Code/User/globalStorage")
        else:
            vscode_ext_path = os.path.expanduser("~/.vscode/extensions")
        
        if os.path.exists(vscode_ext_path):
            # 检查是否有GitHub Copilot扩展
            for item in os.listdir(vscode_ext_path):
                if "github.copilot" in item.lower():
                    return {
                        "install_path_found": True,
                        "install_path": os.path.join(vscode_ext_path, item)
                    }
        
        return None
    
    def _detect_tabnine_app(self, tool_id: str, tool_name: str) -> Optional[Dict]:
        """检测Tabnine应用"""
        if tool_id != "tabnine":
            return None
        
        if self.system == "windows":
            paths = [
                os.path.expanduser("~/AppData/Local/TabNine/TabNine.exe"),
                "C:/Program Files/TabNine/TabNine.exe"
            ]
        elif self.system == "darwin":
            paths = [
                "/Applications/TabNine.app",
                os.path.expanduser("~/Applications/TabNine.app")
            ]
        else:
            paths = [
                "/usr/bin/tabnine",
                os.path.expanduser("~/.local/bin/tabnine")
            ]
        
        for path in paths:
            if os.path.exists(path):
                return {
                    "executable_found": True,
                    "executable_path": path,
                    "install_path_found": True,
                    "install_path": os.path.dirname(path)
                }
        
        return None
    
    def get_launch_command(self, tool_id: str, project_path: str) -> List[str]:
        """获取工具启动命令"""
        if tool_id == "cursor":
            # Cursor需要打开项目目录
            if self.system == "windows":
                return ["cursor", project_path]
            else:
                return ["cursor", project_path]
        
        elif tool_id == "aider":
            # Aider在项目目录中启动
            return ["aider", "--model", "deepseek-chat"]
        
        elif tool_id == "claude_code":
            # Claude Code
            return ["claude"]
        
        elif tool_id == "codex":
            # GitHub Copilot CLI
            return ["github-copilot"]
        
        elif tool_id == "tabnine":
            # Tabnine
            return ["tabnine"]
        
        else:
            # 默认使用工具ID作为命令
            return [tool_id]
    
    def check_tool_availability(self, tool_id: str) -> bool:
        """检查工具是否可用"""
        for tool_def in self.tools:
            if tool_def["id"] == tool_id:
                tool_info = self._detect_tool(tool_def)
                return tool_info is not None
        
        return False


def main():
    """测试函数"""
    detector = ToolDetector()
    
    print("🔍 正在检测AI编程工具...")
    tools = detector.detect_installed_tools()
    
    if not tools:
        print("❌ 未检测到任何AI编程工具")
        return
    
    print(f"\n✅ 检测到 {len(tools)} 个工具:")
    print("-" * 60)
    
    for tool in tools:
        print(f"📦 {tool['name']} ({tool['id']})")
        print(f"   描述: {tool['description']}")
        
        if tool['command_path']:
            print(f"   命令路径: {tool['command_path']}")
        if tool['install_path']:
            print(f"   安装路径: {tool['install_path']}")
        if tool['executable_path']:
            print(f"   可执行文件: {tool['executable_path']}")
        
        print()


if __name__ == "__main__":
    main()