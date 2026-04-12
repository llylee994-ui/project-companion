#!/usr/bin/env python3
"""
AI Coding Companion - 主入口
OpenClaw Skill 执行时调用
监控 Aider 日志文件，检测工作完成，发送通知
"""

import sys
import os
import time
import signal
from typing import Dict, Any, List

# 添加 src 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.strategies.log_monitor import LogFileMonitor
from src.detector import CompletionDetector
from src.notifier import Notifier
from src.utils import load_config


class AiderMonitor:
    """Aider 监控器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.projects = config.get("projects", [])
        self.monitoring_config = config.get("monitoring", {})
        self.notification_config = config.get("notification", {})
        
        # 运行标志
        self.running = False
        
        # 监控器字典：项目名 -> (monitor, detector)
        self.monitors: Dict[str, Any] = {}
        
        # 通知器
        self.notifier = Notifier(self.notification_config.get("channels", []))
    
    def setup_monitors(self) -> bool:
        """设置所有项目的监控器"""
        print(f"设置 {len(self.projects)} 个项目的监控器...")
        
        for project in self.projects:
            if not project.get("enabled", True):
                print(f"跳过禁用项目: {project['name']}")
                continue
            
            project_name = project["name"]
            tool_type = project.get("tool", "aider")
            
            if tool_type != "aider":
                print(f"警告: 项目 {project_name} 使用不支持的工具类型: {tool_type}")
                print(f"当前 MVP 只支持 Aider")
                continue
            
            # 获取 Aider 配置
            aider_config = project.get("aider_config", {})
            
            # 自动检测日志文件路径（如果未指定或指定了默认值）
            log_path = aider_config.get("log_path", "")
            auto_detect = aider_config.get("auto_detect", True)
            
            if not log_path or log_path in ["~/.aider/history", "~/.aider/chat.history.md"] or auto_detect:
                print(f"为项目 {project_name} 自动检测 Aider 日志文件...")
                try:
                    from src.aider_detector import auto_detect_aider_config
                    detected_config = auto_detect_aider_config()
                    log_path = detected_config.get("log_path", log_path)
                    
                    # 更新完成标记（如果检测到的配置中有）
                    completion_markers = detected_config.get("completion_markers", 
                        aider_config.get("completion_markers", [
                            "Added",
                            "Committed",
                            "^>"  # 正则：以 > 开头的行（提示符）
                        ])
                    )
                    
                    print(f"  自动检测到日志文件: {log_path}")
                    
                except ImportError as e:
                    print(f"  自动检测失败: {e}")
                    completion_markers = aider_config.get("completion_markers", [
                        "Added",
                        "Committed",
                        "^>"
                    ])
            else:
                completion_markers = aider_config.get("completion_markers", [
                    "Added",
                    "Committed",
                    "^>"
                ])
            
            # 如果还是没有日志路径，使用默认值
            if not log_path:
                log_path = "~/.aider/chat.history.md"
                print(f"  使用默认日志路径: {log_path}")
            
            # 创建监控器
            monitor = LogFileMonitor()
            if not monitor.start({"log_path": log_path}):
                print(f"错误: 无法启动项目 {project_name} 的监控器")
                continue
            
            # 创建检测器
            detector = CompletionDetector(completion_markers)
            
            # 存储
            self.monitors[project_name] = {
                "monitor": monitor,
                "detector": detector,
                "config": project,
                "last_activity": time.time(),
                "log_path": log_path
            }
            
            print(f"[OK] 已设置项目监控: {project_name}")
            print(f"  日志路径: {log_path}")
            print(f"  完成标记: {completion_markers}")
        
        return len(self.monitors) > 0
    
    def check_project(self, project_name: str, project_info: Dict[str, Any]) -> bool:
        """检查单个项目"""
        monitor = project_info["monitor"]
        detector = project_info["detector"]
        config = project_info["config"]
        
        # 检查日志文件
        result = monitor.check()
        
        if result["status"] == "error":
            print(f"错误: 项目 {project_name} 监控失败: {result['metadata'].get('error', '未知错误')}")
            return False
        
        if result["status"] == "working" and result["output"]:
            # 有新内容，喂给检测器
            detection = detector.feed(result["output"])
            
            if detection["completed"]:
                print(f"\n🎉 检测到项目 {project_name} 完成工作!")
                print(f"   耗时: {detection['duration']}")
                print(f"   匹配标记: {detection['matched_marker']}")
                print(f"   摘要: {detection['summary']}")
                
                # 发送通知
                if self.notification_config.get("enabled", True):
                    notify_result = self.notifier.send_aider_completion(
                        project_name=project_name,
                        duration=detection["duration"],
                        summary=detection["summary"]
                    )
                    print(f"   通知发送结果: {notify_result}")
                
                # 重置检测器，准备下一次
                detector.start_session()
                project_info["last_activity"] = time.time()
                
                return True
        
        # 检查会话超时
        check_interval = self.monitoring_config.get("check_interval", 2)
        max_session_duration = self.monitoring_config.get("max_session_duration", 1800)  # 30分钟
        
        if detector.is_session_active():
            session_duration = time.time() - project_info["last_activity"]
            if session_duration > max_session_duration:
                print(f"项目 {project_name} 会话超时 ({max_session_duration}秒)，重置检测器")
                detector.reset()
        
        return False
    
    def run(self):
        """运行主监控循环"""
        if not self.setup_monitors():
            print("错误: 没有可监控的项目")
            return
        
        print(f"\n{'='*60}")
        print("AI Coding Companion 监控已启动")
        print(f"监控项目数: {len(self.monitors)}")
        print(f"检查间隔: {self.monitoring_config.get('check_interval', 2)} 秒")
        print(f"最大会话时长: {self.monitoring_config.get('max_session_duration', 1800)} 秒")
        print(f"{'='*60}\n")
        
        self.running = True
        
        # 设置信号处理
        def signal_handler(sig, frame):
            print(f"\n接收到信号 {sig}，正在停止监控...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            while self.running:
                check_interval = self.monitoring_config.get("check_interval", 2)
                
                for project_name, project_info in list(self.monitors.items()):
                    self.check_project(project_name, project_info)
                
                # 等待下一次检查
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n用户中断，正在停止...")
        except Exception as e:
            print(f"\n监控循环发生错误: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        print("\n正在清理资源...")
        
        for project_name, project_info in self.monitors.items():
            monitor = project_info["monitor"]
            monitor.stop()
            print(f"[OK] 已停止项目监控: {project_name}")
        
        print("监控已完全停止")


def main():
    """主函数"""
    # 加载配置
    config = load_config("config.yaml")
    if not config:
        print("错误: 无法加载配置文件 config.yaml")
        print("请确保配置文件存在且格式正确")
        return 1
    
    # 检查配置版本
    version = config.get("version", "1.0")
    print(f"AI Coding Companion v{version}")
    
    # 检查项目配置
    projects = config.get("projects", [])
    if not projects:
        print("错误: 配置文件中没有项目配置")
        print("请在 config.yaml 中添加 projects 配置")
        return 1
    
    # 创建并运行监控器
    monitor = AiderMonitor(config)
    monitor.run()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
