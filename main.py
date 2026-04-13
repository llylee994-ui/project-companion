#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
AI Coding Companion - 主入口
OpenClaw Skill 执行时调用
监控 Aider 日志文件，检测工作完成，发送通知
"""

import sys
import os
import time
import signal
import io
from typing import Dict, Any, List

# 设置 UTF-8 编码（Windows 兼容）
# 注意：为了确保实时输出，我们使用 line_buffering=True 并设置环境变量 PYTHONUNBUFFERED
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

# 辅助函数：确保输出立即刷新
def print_flush(*args, **kwargs):
    """立即刷新输出的 print 函数"""
    print(*args, **kwargs)
    sys.stdout.flush()

# 添加 src 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.strategies.log_monitor import LogFileMonitor
from src.strategies.terminal_monitor import TerminalMonitor
from src.detector import CompletionDetector
from src.notifier import Notifier
from src.permission_detector import PermissionDetector, PermissionDecision
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
            
            # 检查是否使用终端监控
            terminal_config = project.get("terminal_config", {})
            use_terminal_monitor = terminal_config.get("enabled", False)
            
            if use_terminal_monitor:
                # 使用终端监控
                success = self._setup_terminal_monitor(project)
                if not success:
                    print(f"错误: 无法启动项目 {project_name} 的终端监控器")
                    continue
            else:
                # 使用日志监控（现有逻辑）
                if tool_type != "aider":
                    print(f"警告: 项目 {project_name} 使用不支持的工具类型: {tool_type}")
                    print(f"当前日志监控只支持 Aider")
                    continue
                
                success = self._setup_log_monitor(project)
                if not success:
                    print(f"错误: 无法启动项目 {project_name} 的日志监控器")
                    continue
        
        return len(self.monitors) > 0
    
    def _setup_log_monitor(self, project: Dict[str, Any]) -> bool:
        """设置日志文件监控"""
        project_name = project["name"]
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
        from src.strategies.log_monitor import LogFileMonitor
        monitor = LogFileMonitor()
        if not monitor.start({"log_path": log_path}):
            return False
        
        # 创建检测器
        from src.detector import CompletionDetector
        detector = CompletionDetector(completion_markers)
        
        # 创建权限检测器
        from src.permission_detector import PermissionDetector
        permission_detector = PermissionDetector(self.config)
        
        # 存储
        self.monitors[project_name] = {
            "monitor": monitor,
            "detector": detector,
            "permission_detector": permission_detector,
            "config": project,
            "last_activity": time.time(),
            "log_path": log_path,
            "last_permission_notification": 0,
            "monitor_type": "log"  # 标记监控类型
        }
        
        print(f"[OK] 已设置日志监控: {project_name}")
        print(f"  日志路径: {log_path}")
        print(f"  完成标记: {completion_markers}")
        
        return True
    
    def _setup_terminal_monitor(self, project: Dict[str, Any]) -> bool:
        """设置终端监控"""
        project_name = project["name"]
        terminal_config = project.get("terminal_config", {})
        project_path = project.get("path", ".")
        
        # 获取命令配置
        command = terminal_config.get("command", "aider")
        if isinstance(command, str):
            command = [command]
        
        # 获取额外参数
        args = terminal_config.get("args", [])
        if args:
            command.extend(args)
        
        # 获取环境变量
        env = terminal_config.get("env", {})
        
        # 获取自动响应配置
        auto_response_config = terminal_config.get("auto_response", {})
        auto_response_enabled = auto_response_config.get("enabled", False)
        default_response = auto_response_config.get("default", "y")
        
        # 创建权限检测器（必须先创建，因为后面会用到）
        from src.permission_detector import PermissionDetector
        permission_detector = PermissionDetector(self.config)
        
        # 创建监控器
        from src.strategies.terminal_monitor import TerminalMonitor
        monitor = TerminalMonitor()
        
        # 准备回调函数
        def on_output_callback(line: str):
            # 这里可以处理输出，但主要逻辑在 check_project 中
            pass
        
        def on_permission_callback(line: str, permission_prompt=None):
            # 终端监控中检测到权限询问
            if project_name in self.monitors:
                project_info = self.monitors[project_name]
                
                # 如果回调没有提供权限提示，尝试检测
                if not permission_prompt:
                    perm_detector = project_info["permission_detector"]
                    permission_prompt = perm_detector.detect(line)
                
                if permission_prompt:
                    self._handle_permission_prompt(project_name, project_info, permission_prompt)
                    
                    # 注意：自动响应现在在 TerminalMonitor 内部处理
                    # 这里只记录日志
                    if auto_response_enabled:
                        print(f"  检测到权限询问，自动响应已启用")
        
        # 启动监控器
        monitor_config = {
            "command": command,
            "project_path": project_path,
            "env": env,
            "on_output": on_output_callback,
            "on_permission": on_permission_callback,
            "permission_detector": permission_detector,
            "auto_response_config": auto_response_config
        }
        
        if not monitor.start(monitor_config):
            return False
        
        # 创建检测器（使用终端特定的完成标记）
        from src.detector import CompletionDetector
        completion_markers = terminal_config.get("completion_markers", [
            "Added",
            "Committed",
            "^>",  # 提示符
            "✓",   # 完成标记
            "Done",
            "Finished",
            "Completed"
        ])
        detector = CompletionDetector(completion_markers)
        
        # 存储
        self.monitors[project_name] = {
            "monitor": monitor,
            "detector": detector,
            "permission_detector": permission_detector,
            "config": project,
            "last_activity": time.time(),
            "terminal_config": terminal_config,
            "last_permission_notification": 0,
            "monitor_type": "terminal",  # 标记监控类型
            "auto_response_enabled": auto_response_enabled,
            "auto_response_config": auto_response_config
        }
        
        print(f"[OK] 已设置终端监控: {project_name}")
        print(f"  命令: {' '.join(command)}")
        print(f"  项目路径: {project_path}")
        print(f"  自动响应: {'启用' if auto_response_enabled else '禁用'}")
        
        return True
    
    def _should_auto_allow(self, permission_prompt, auto_response_config: Dict[str, Any]) -> bool:
        """检查是否应该自动允许权限请求"""
        files = getattr(permission_prompt, 'files', [])
        
        # 检查白名单
        whitelist = auto_response_config.get("whitelist", [])
        if whitelist:
            import re
            for file in files:
                for pattern in whitelist:
                    if re.match(pattern, file):
                        return True
        
        # 检查黑名单
        blacklist = auto_response_config.get("blacklist", [])
        if blacklist:
            import re
            for file in files:
                for pattern in blacklist:
                    if re.match(pattern, file):
                        return False
        
        # 默认根据配置决定
        return auto_response_config.get("default_allow", True)
    
    def check_project(self, project_name: str, project_info: Dict[str, Any]) -> bool:
        """检查单个项目"""
        monitor = project_info["monitor"]
        detector = project_info["detector"]
        permission_detector = project_info["permission_detector"]
        config = project_info["config"]
        monitor_type = project_info.get("monitor_type", "log")
        
        # 检查监控器状态
        result = monitor.check()
        
        if result["status"] == "error":
            error_msg = result['metadata'].get('error', '未知错误')
            print(f"错误: 项目 {project_name} 监控失败: {error_msg}")
            
            # 对于终端监控，如果进程死亡，可能需要重启
            if monitor_type == "terminal" and "进程未启动" in error_msg:
                print(f"  终端进程已结束，尝试重启...")
                # 这里可以添加重启逻辑
            return False
        
        # 处理输出内容
        if result["status"] == "working" and result["output"]:
            new_content = result["output"]
            
            # 1. 检查权限询问（对于日志监控）
            # 注意：终端监控的权限检测在回调中处理
            if monitor_type == "log":
                permission_prompt = permission_detector.detect(new_content)
                if permission_prompt:
                    self._handle_permission_prompt(project_name, project_info, permission_prompt)
            
            # 2. 检查工作完成
            detection = detector.feed(new_content)
            
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
    
    def _handle_permission_prompt(self, 
                                 project_name: str, 
                                 project_info: Dict[str, Any], 
                                 prompt: Any) -> None:
        """
        处理权限提示
        
        Args:
            project_name: 项目名称
            project_info: 项目信息
            prompt: 权限提示对象
        """
        permission_detector = project_info["permission_detector"]
        
        # 检查是否需要通知（避免重复通知）
        current_time = time.time()
        last_notification = project_info.get("last_permission_notification", 0)
        notification_cooldown = 60  # 60秒冷却时间
        
        if current_time - last_notification < notification_cooldown:
            return
        
        # 检查是否应该通知
        should_notify = permission_detector.should_notify(prompt)
        
        if should_notify:
            # 做出决策
            decision = permission_detector.make_decision(prompt)
            decision_str = decision.value if decision else "ask"
            
            # 发送通知
            if self.notification_config.get("enabled", True):
                auto_decision = decision in [PermissionDecision.ALLOW, PermissionDecision.DENY, PermissionDecision.AUTO_APPROVE]
                
                notify_result = self.notifier.send_permission_request(
                    project_name=project_name,
                    permission_type=prompt.permission_type.value,
                    prompt_text=prompt.prompt_text,
                    files=prompt.files,
                    decision=decision_str,
                    auto_decision=auto_decision
                )
                
                print(f"\n🔐 检测到权限请求: {project_name}")
                print(f"   类型: {prompt.permission_type.value}")
                print(f"   决策: {decision_str}")
                print(f"   通知发送结果: {notify_result}")
                
                # 更新最后通知时间
                project_info["last_permission_notification"] = current_time
                
                # 显示决策消息
                decision_msg = permission_detector.get_decision_message(prompt, decision)
                print(f"   {decision_msg}")
        else:
            # 自动处理，不通知
            decision = permission_detector.make_decision(prompt)
            if decision in [PermissionDecision.ALLOW, PermissionDecision.DENY]:
                print(f"\n🤖 自动处理权限请求: {project_name}")
                print(f"   类型: {prompt.permission_type.value}")
                print(f"   决策: {decision.value}")
                
                decision_msg = permission_detector.get_decision_message(prompt, decision)
                print(f"   {decision_msg}")
    
    def run(self):
        """运行主监控循环"""
        if not self.setup_monitors():
            print("错误: 没有可监控的项目")
            return
        
        print(f"\n{'='*60}", flush=True)
        print("AI Coding Companion 监控已启动", flush=True)
        print(f"监控项目数: {len(self.monitors)}", flush=True)
        print(f"检查间隔: {self.monitoring_config.get('check_interval', 2)} 秒", flush=True)
        print(f"最大会话时长: {self.monitoring_config.get('max_session_duration', 1800)} 秒", flush=True)
        print(f"{'='*60}\n", flush=True)
        
        self.running = True
        
        # 设置信号处理
        def signal_handler(sig, frame):
            print(f"\n接收到信号 {sig}，正在停止监控...", flush=True)
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
            print("\n用户中断，正在停止...", flush=True)
        except Exception as e:
            print(f"\n监控循环发生错误: {e}", flush=True)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        print("\n正在清理资源...", flush=True)
        
        for project_name, project_info in self.monitors.items():
            monitor = project_info["monitor"]
            monitor.stop()
            print(f"[OK] 已停止项目监控: {project_name}", flush=True)
        
        print("监控已完全停止", flush=True)


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
