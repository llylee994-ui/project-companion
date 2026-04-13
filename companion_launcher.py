#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Coding Companion - 一体化启动器
用户只需运行此程序，即可完成工具选择、启动和监控
"""

import os
import sys
import time
import signal
import threading
import io
from typing import Dict, Optional

# Windows编码处理
if sys.platform == 'win32':
    # 强制设置环境变量以确保无缓冲输出
    os.environ['PYTHONUNBUFFERED'] = '1'
    
    # 创建无缓冲的 TextIOWrapper
    # write_through=True 确保立即写入底层缓冲区
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, 
        encoding='utf-8', 
        errors='replace', 
        line_buffering=True,
        write_through=True
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, 
        encoding='utf-8', 
        errors='replace', 
        line_buffering=True,
        write_through=True
    )

# 添加src到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tool_detector import ToolDetector
from src.tool_selector import ToolSelector
from src.tool_launcher import ToolManager, create_tool_config
from src.monitor_manager import MonitorManager


class CompanionLauncher:
    """一体化启动器"""
    
    def __init__(self):
        self.detector = ToolDetector()
        self.selector = ToolSelector()
        self.tool_manager = ToolManager()
        self.monitor_manager = MonitorManager()
        self.running = False
        self.selected_tool = None
        self.project_path = None
        self.config = None
    
    def run(self):
        """运行启动器"""
        print("=" * 60)
        print("🤖 AI Coding Companion - 一体化启动器")
        print("=" * 60)
        print("自动检测工具 → 选择配置 → 启动工具 → 监控完成 → 发送通知")
        print("=" * 60)
        
        try:
            # 1. 检测并选择工具
            selection = self._select_tool_and_config()
            if not selection:
                print("\n❌ 配置已取消")
                return
            
            # 2. 生成配置
            self.config = self._generate_config(selection)
            if not self.config:
                print("\n❌ 配置生成失败")
                return
            
            # 3. 保存配置
            if not self.monitor_manager.save_config(self.config):
                print("\n❌ 配置保存失败")
                return
            
            # 4. 启动工具
            if not self._launch_tool(selection):
                print("\n❌ 工具启动失败")
                return
            
            # 5. 启动监控
            if not self._start_monitoring():
                print("\n❌ 监控启动失败")
                return
            
            # 6. 运行主循环
            self._main_loop()
            
        except KeyboardInterrupt:
            print("\n\n🛑 用户中断")
        except Exception as e:
            print(f"\n❌ 启动器运行出错: {e}")
        finally:
            self.cleanup()
    
    def _select_tool_and_config(self) -> Optional[Dict]:
        """选择工具和配置"""
        print("\n🔍 步骤1: 检测并选择AI编程工具")
        print("-" * 40)
        
        # 使用现有的工具选择器
        selection = self.selector.detect_and_select()
        
        if selection:
            self.selected_tool = selection["tool"]
            self.project_path = selection["project_path"]
            
            print("\n✅ 选择完成:")
            print(f"   工具: {self.selected_tool['name']}")
            print(f"   批准模式: {selection['approval_mode']}")
            print(f"   项目路径: {self.project_path}")
            print(f"   通知: {'启用' if selection['notification']['enabled'] else '禁用'}")
        
        return selection
    
    def _generate_config(self, selection: Dict) -> Optional[Dict]:
        """生成监控配置"""
        print("\n⚙️  步骤2: 生成监控配置")
        print("-" * 40)
        
        # 使用监控管理器生成配置
        config = self.monitor_manager.generate_config(
            tool_info=selection["tool"],
            project_path=selection["project_path"],
            approval_mode=selection["approval_mode"],
            notification_enabled=selection["notification"]["enabled"],
            aider_config=selection.get("aider_config", {})
        )
        
        if config:
            print("✅ 配置生成成功")
            return config
        
        return None
    
    def _launch_tool(self, selection: Dict) -> bool:
        """启动AI工具"""
        print("\n🚀 步骤3: 启动AI编程工具")
        print("-" * 40)
        
        tool_info = selection["tool"]
        approval_mode = selection["approval_mode"]
        aider_config = selection.get("aider_config", {})
        
        # 创建工具配置
        tool_config = create_tool_config(tool_info, approval_mode, aider_config)
        
        # 启动工具
        success = self.tool_manager.launch(
            tool_id=tool_info["id"],
            tool_config=tool_config,
            project_path=self.project_path
        )
        
        if success:
            print(f"✅ {tool_info['name']} 已启动")
            return True
        
        return False
    
    def _start_monitoring(self) -> bool:
        """启动监控"""
        print("\n👁️  步骤4: 启动监控进程")
        print("-" * 40)
        
        # 启动监控
        success = self.monitor_manager.start_monitoring()
        
        if success:
            print("✅ 监控已启动")
            print("\n📊 监控信息:")
            status = self.monitor_manager.get_status()
            print(f"   运行状态: {'运行中' if status['running'] else '未运行'}")
            if status.get('pid'):
                print(f"   进程ID: {status['pid']}")
            print(f"   配置文件: {status['config_path']}")
            return True
        
        return False
    
    def _main_loop(self):
        """主循环"""
        print("\n" + "=" * 60)
        print("🎯 启动完成! AI Coding Companion 正在运行")
        print("=" * 60)
        print("\n📋 运行信息:")
        print(f"   工具: {self.selected_tool['name']}")
        print(f"   项目: {self.project_path}")
        print(f"   监控: 运行中")
        print("\n📝 使用说明:")
        print("   1. 现在可以使用选中的AI工具进行编程")
        print("   2. 工具完成工作时会自动发送通知")
        print("   3. 按 Ctrl+C 停止所有进程")
        print("\n" + "=" * 60)
        
        self.running = True
        
        # 设置信号处理
        def signal_handler(sig, frame):
            print(f"\n接收到信号 {sig}，正在停止...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 主循环
        try:
            while self.running:
                # 检查工具状态
                running_tools = self.tool_manager.get_running_tools()
                if not running_tools:
                    print("\n⚠️  AI工具已停止运行")
                    break
                
                # 检查监控状态
                if not self.monitor_manager.is_running():
                    print("\n⚠️  监控进程已停止")
                    break
                
                # 等待
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n\n🛑 用户中断")
        except Exception as e:
            print(f"\n❌ 主循环出错: {e}")
    
    def cleanup(self):
        """清理资源"""
        print("\n🧹 正在清理资源...")
        
        # 停止监控
        self.monitor_manager.stop_monitoring()
        
        # 停止所有工具
        self.tool_manager.stop_all()
        
        print("✅ 清理完成")
    
    def quick_start(self, tool_id: str = None, project_path: str = None):
        """快速启动（使用默认配置）"""
        print("🚀 快速启动模式")
        
        # 检测工具
        tools = self.detector.detect_installed_tools()
        
        if not tools:
            print("❌ 未检测到任何AI编程工具")
            return False
        
        # 选择工具
        if tool_id:
            selected_tool = None
            for tool in tools:
                if tool["id"] == tool_id:
                    selected_tool = tool
                    break
            
            if not selected_tool:
                print(f"❌ 未找到工具: {tool_id}")
                return False
        else:
            # 选择第一个检测到的工具
            selected_tool = tools[0]
        
        # 使用当前目录作为项目路径
        if not project_path:
            project_path = os.getcwd()
        
        # 生成配置
        config = self.monitor_manager.generate_config(
            tool_info=selected_tool,
            project_path=project_path,
            approval_mode="auto",
            notification_enabled=True
        )
        
        if not config:
            return False
        
        # 保存配置
        if not self.monitor_manager.save_config(config):
            return False
        
        # 启动工具
        tool_config = create_tool_config(selected_tool, "auto")
        success = self.tool_manager.launch(
            tool_id=selected_tool["id"],
            tool_config=tool_config,
            project_path=project_path
        )
        
        if not success:
            return False
        
        # 启动监控
        return self.monitor_manager.start_monitoring()


def main():
    """主函数"""
    launcher = CompanionLauncher()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "quick":
            # 快速启动
            tool_id = sys.argv[2] if len(sys.argv) > 2 else None
            project_path = sys.argv[3] if len(sys.argv) > 3 else None
            
            if launcher.quick_start(tool_id, project_path):
                print("\n✅ 快速启动成功!")
                print("\n按 Ctrl+C 停止")
                
                # 保持运行
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 停止")
                    launcher.cleanup()
            else:
                print("❌ 快速启动失败")
        
        elif command == "status":
            # 显示状态
            print("📊 系统状态:")
            
            # 工具状态
            tool_manager = ToolManager()
            tool_status = tool_manager.get_status()
            print(f"\n🔧 工具状态:")
            for tool_id, status in tool_status.items():
                print(f"   {tool_id}: {'运行中' if status['running'] else '未运行'}")
            
            # 监控状态
            monitor_manager = MonitorManager()
            monitor_status = monitor_manager.get_status()
            print(f"\n👁️  监控状态:")
            print(f"   运行状态: {'运行中' if monitor_status['running'] else '未运行'}")
            print(f"   配置文件: {monitor_status['config_path']}")
            print(f"   配置加载: {'是' if monitor_status['config_loaded'] else '否'}")
        
        elif command == "stop":
            # 停止所有
            print("🛑 停止所有进程...")
            
            tool_manager = ToolManager()
            monitor_manager = MonitorManager()
            
            monitor_manager.stop_monitoring()
            tool_manager.stop_all()
            
            print("✅ 已停止所有进程")
        
        elif command == "help":
            # 显示帮助
            print("🤖 AI Coding Companion 启动器")
            print("\n使用方法:")
            print("  python companion_launcher.py           # 交互式启动")
            print("  python companion_launcher.py quick     # 快速启动（使用第一个检测到的工具）")
            print("  python companion_launcher.py quick aider ~/projects/my-app  # 快速启动指定工具")
            print("  python companion_launcher.py status    # 显示状态")
            print("  python companion_launcher.py stop      # 停止所有进程")
            print("  python companion_launcher.py help      # 显示帮助")
        
        else:
            print(f"❌ 未知命令: {command}")
            print("使用 'python companion_launcher.py help' 查看帮助")
    
    else:
        # 交互式启动
        launcher.run()


if __name__ == "__main__":
    main()