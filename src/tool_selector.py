# -*- coding: utf-8 -*-
"""
工具选择器 - 交互式选择AI编程工具和配置
"""

import os
import sys
from typing import Dict, List, Optional
from .tool_detector import ToolDetector


class ToolSelector:
    """交互式工具选择器"""
    
    def __init__(self):
        self.detector = ToolDetector()
        self.available_tools = []
    
    def detect_and_select(self) -> Optional[Dict]:
        """检测并选择工具"""
        print("🔍 正在检测AI编程工具...")
        self.available_tools = self.detector.detect_installed_tools()
        
        if not self.available_tools:
            print("\n❌ 未检测到任何AI编程工具")
            print("\n请安装以下工具之一:")
            print("1. Cursor - https://cursor.sh")
            print("2. Aider - pip install aider-chat")
            print("3. Claude Code")
            print("4. 其他兼容工具")
            return None
        
        print(f"\n✅ 检测到 {len(self.available_tools)} 个工具:")
        print("-" * 60)
        
        for i, tool in enumerate(self.available_tools, 1):
            status = "✅" if any([tool['command_found'], tool['install_path_found'], tool['executable_found']]) else "⚠️"
            print(f"{i}. {status} {tool['name']} - {tool['description']}")
        
        print("-" * 60)
        
        # 选择工具
        selected_tool = self._select_tool()
        if not selected_tool:
            return None
        
        # 选择批准模式
        approval_mode = self._select_approval_mode()
        
        # 输入项目路径
        project_path = self._input_project_path()
        
        # 配置Aider模型（如果选择了Aider）
        aider_config = {}
        if selected_tool["id"] == "aider":
            aider_config = self._configure_aider_model()
        
        # 配置通知
        notification_config = self._configure_notification()
        
        return {
            "tool": selected_tool,
            "approval_mode": approval_mode,
            "project_path": project_path,
            "aider_config": aider_config,
            "notification": notification_config
        }
    
    def _select_tool(self) -> Optional[Dict]:
        """选择工具"""
        while True:
            try:
                choice = input(f"\n请选择要使用的工具 (1-{len(self.available_tools)}, 或输入q退出): ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(self.available_tools):
                    selected = self.available_tools[index]
                    print(f"\n✅ 已选择: {selected['name']}")
                    
                    # 显示工具详情
                    print(f"\n工具详情:")
                    print(f"  ID: {selected['id']}")
                    print(f"  描述: {selected['description']}")
                    
                    if selected['command_path']:
                        print(f"  命令: {selected['command_path']}")
                    if selected['install_path']:
                        print(f"  安装路径: {selected['install_path']}")
                    
                    return selected
                else:
                    print(f"❌ 请输入 1-{len(self.available_tools)} 之间的数字")
                    
            except ValueError:
                print("❌ 请输入有效的数字")
            except KeyboardInterrupt:
                print("\n\n操作已取消")
                return None
    
    def _select_approval_mode(self) -> str:
        """选择批准模式"""
        print("\n📋 请选择权限批准模式:")
        print("1. 自动批准 (推荐) - 自动批准所有安全操作")
        print("2. 询问模式 - 每次权限请求都询问")
        print("3. 静默模式 - 不处理权限请求")
        print("4. 智能模式 - 根据文件类型自动决定")
        
        modes = {
            "1": "auto",
            "2": "ask",
            "3": "silent",
            "4": "smart"
        }
        
        while True:
            try:
                choice = input("\n选择模式 (1-4, 默认1): ").strip()
                if not choice:
                    choice = "1"
                
                if choice in modes:
                    mode = modes[choice]
                    mode_names = {
                        "auto": "自动批准",
                        "ask": "询问模式",
                        "silent": "静默模式",
                        "smart": "智能模式"
                    }
                    print(f"✅ 已选择: {mode_names[mode]}")
                    return mode
                else:
                    print("❌ 请输入 1-4 之间的数字")
                    
            except KeyboardInterrupt:
                print("\n\n操作已取消")
                return "auto"
    
    def _input_project_path(self) -> str:
        """输入项目路径"""
        print("\n📁 项目路径配置:")
        print("提示: 输入项目目录路径，或按回车使用当前目录")
        
        default_path = os.getcwd()
        
        while True:
            try:
                path = input(f"\n项目路径 [{default_path}]: ").strip()
                
                if not path:
                    path = default_path
                    print(f"✅ 使用当前目录: {path}")
                    return path
                
                # 扩展用户目录
                path = os.path.expanduser(path)
                
                # 检查路径是否存在
                if os.path.exists(path):
                    if os.path.isdir(path):
                        print(f"✅ 项目路径: {path}")
                        return path
                    else:
                        print("❌ 路径不是目录")
                else:
                    create = input(f"目录不存在，是否创建? (y/n): ").strip().lower()
                    if create == 'y':
                        os.makedirs(path, exist_ok=True)
                        print(f"✅ 已创建目录: {path}")
                        return path
                    else:
                        print("❌ 请重新输入路径")
                        
            except KeyboardInterrupt:
                print("\n\n操作已取消")
                return default_path
    
    def _configure_aider_model(self) -> Dict:
        """配置Aider模型"""
        print("\n🤖 Aider模型配置:")
        print("提示: Aider需要指定使用的AI模型")
        print("常用模型选项:")
        print("1. deepseek-chat (默认，免费)")
        print("2. deepseek/deepseek-chat (官方)")
        print("3. gpt-4 (OpenAI)")
        print("4. claude-3 (Anthropic)")
        print("5. 自定义模型")
        
        model_options = {
            "1": "deepseek-chat",
            "2": "deepseek/deepseek-chat", 
            "3": "gpt-4",
            "4": "claude-3",
            "5": "custom"
        }
        
        while True:
            try:
                choice = input("\n选择模型 (1-5, 默认1): ").strip()
                if not choice:
                    choice = "1"
                
                if choice in model_options:
                    model = model_options[choice]
                    
                    if model == "custom":
                        custom_model = input("请输入自定义模型名称: ").strip()
                        if custom_model:
                            model = custom_model
                        else:
                            print("❌ 请输入有效的模型名称")
                            continue
                    
                    print(f"✅ 已选择模型: {model}")
                    
                    # 询问是否添加其他参数
                    extra_args = []
                    add_more = input("是否添加其他Aider参数? (y/n, 默认n): ").strip().lower()
                    if add_more == 'y':
                        print("提示: 可以添加如 --api-key, --temperature 等参数")
                        print("格式: --参数名 值 (多个参数用空格分隔)")
                        args_input = input("请输入额外参数: ").strip()
                        if args_input:
                            # 简单分割参数
                            import shlex
                            extra_args = shlex.split(args_input)
                    
                    return {
                        "model": model,
                        "extra_args": extra_args
                    }
                else:
                    print("❌ 请输入 1-5 之间的数字")
                    
            except KeyboardInterrupt:
                print("\n\n使用默认模型配置")
                return {"model": "deepseek-chat", "extra_args": []}
    
    def _configure_notification(self) -> Dict:
        """配置通知"""
        print("\n🔔 通知配置:")
        print("提示: 按回车使用默认配置")
        
        # 默认配置
        config = {
            "enabled": True,
            "channels": []
        }
        
        try:
            enable = input("启用通知? (y/n, 默认y): ").strip().lower()
            if enable == 'n':
                config["enabled"] = False
                print("✅ 通知已禁用")
                return config
            
            print("✅ 通知已启用")
            
            # 这里可以添加更多通知渠道配置
            # 目前使用默认的飞书配置
            
        except KeyboardInterrupt:
            print("\n\n使用默认通知配置")
        
        return config
    
    def create_monitor_config(self, selection: Dict) -> Dict:
        """创建监控配置"""
        tool = selection["tool"]
        approval_mode = selection["approval_mode"]
        project_path = selection["project_path"]
        aider_config = selection.get("aider_config", {})
        
        # 构建配置
        config = {
            "version": "2.0",
            "projects": [
                {
                    "name": f"{tool['name']}监控",
                    "path": project_path,
                    "tool": tool["id"],
                    "enabled": True,
                    "terminal_config": {
                        "enabled": True,
                        "auto_start": True,
                        "command": self._get_tool_command(tool),
                        "args": self._get_tool_args(tool, aider_config),
                        "completion_markers": self._get_completion_markers(tool["id"]),
                        "auto_response": self._get_auto_response_config(approval_mode)
                    }
                }
            ],
            "notification": selection["notification"],
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
    
    def _get_tool_command(self, tool: Dict) -> List[str]:
        """获取工具命令"""
        if tool["id"] == "cursor":
            return ["cursor"]
        elif tool["id"] == "aider":
            return ["aider"]
        elif tool["id"] == "claude_code":
            return ["claude"]
        elif tool["id"] == "tabnine":
            return ["tabnine"]
        else:
            # 默认使用工具名称
            return [tool["id"]]
    
    def _get_tool_args(self, tool: Dict, aider_config: Dict = None) -> List[str]:
        """获取工具参数"""
        if tool["id"] == "aider":
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
    selector = ToolSelector()
    
    print("=" * 60)
    print("AI Coding Companion - 工具选择器")
    print("=" * 60)
    
    selection = selector.detect_and_select()
    
    if selection:
        print("\n" + "=" * 60)
        print("配置摘要:")
        print("=" * 60)
        
        print(f"工具: {selection['tool']['name']}")
        print(f"批准模式: {selection['approval_mode']}")
        print(f"项目路径: {selection['project_path']}")
        print(f"通知: {'启用' if selection['notification']['enabled'] else '禁用'}")
        
        # 生成配置
        config = selector.create_monitor_config(selection)
        
        print("\n✅ 配置完成!")
        print("\n下一步:")
        print("1. 运行 python main.py 启动监控")
        print("2. 开始使用选中的AI工具进行编程")
        print("3. 工作完成时会收到通知")
        
        # 保存配置
        import yaml
        with open("config_auto.yaml", "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        print(f"\n📁 配置已保存到: config_auto.yaml")
        
    else:
        print("\n❌ 配置已取消")


if __name__ == "__main__":
    main()