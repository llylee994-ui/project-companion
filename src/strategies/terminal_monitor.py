# -*- coding: utf-8 -*-
"""
终端监控策略 - 用于实时捕获 AI 工具输出
支持 Aider/Claude/Codex 等工具
"""

import subprocess
import threading
import time
import os
import re
import locale
import sys
from typing import Dict, Any, List, Optional, Callable
from .base import MonitorStrategy


class TerminalMonitor(MonitorStrategy):
    """终端监控策略 - 实时捕获 AI 工具输出"""
    
    def __init__(self, permission_detector=None):
        self.process = None
        self.is_running = False
        self.output_buffer = []
        self.buffer_lock = threading.Lock()
        self.read_thread = None
        self.command = None
        self.project_path = None
        self.env_vars = None
        self.on_output_callback = None
        self.on_permission_callback = None
        self.permission_detector = permission_detector
        self.encoding = self._get_system_encoding()
        self.auto_response_config = None
        self.auto_response_enabled = False
        
    def _get_system_encoding(self) -> str:
        """获取系统编码"""
        try:
            # 尝试获取系统编码
            encoding = locale.getpreferredencoding()
            if not encoding or encoding.lower() == 'ascii':
                encoding = 'utf-8'
            return encoding
        except:
            return 'utf-8'
        
    def get_name(self) -> str:
        return "terminal_monitor"
    
    def start(self, config: Dict[str, Any]) -> bool:
        """
        启动终端监控
        
        Args:
            config: 配置字典，包含:
                - command: 启动命令（列表或字符串）
                - project_path: 项目路径
                - env: 环境变量字典（可选）
                - on_output: 输出回调函数（可选）
                - on_permission: 权限检测回调函数（可选）
                - permission_detector: 权限检测器实例（可选）
                - auto_response_config: 自动回复配置（可选）
                
        Returns:
            bool: 是否成功启动
        """
        try:
            # 获取配置
            self.command = config.get("command", [])
            if isinstance(self.command, str):
                self.command = [self.command]
            
            if not self.command:
                print(f"错误: 未指定启动命令")
                return False
            
            self.project_path = os.path.expanduser(config.get("project_path", "."))
            self.env_vars = config.get("env", {})
            self.on_output_callback = config.get("on_output")
            self.on_permission_callback = config.get("on_permission")
            
            # 获取权限检测器和自动回复配置
            self.permission_detector = config.get("permission_detector", self.permission_detector)
            self.auto_response_config = config.get("auto_response_config", {})
            self.auto_response_enabled = self.auto_response_config.get("enabled", False)
            
            # 准备环境变量
            env = os.environ.copy()
            env.update(self.env_vars)
            
            print(f"启动终端监控: {' '.join(self.command)}")
            print(f"项目路径: {self.project_path}")
            
            # 启动进程
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding=self.encoding,
                errors='replace',  # 使用 replace 而不是 ignore，避免数据丢失
                cwd=self.project_path,
                env=env
            )
            
            # 启动读取线程
            self.is_running = True
            self.output_buffer = []
            self.read_thread = threading.Thread(
                target=self._read_output,
                daemon=True
            )
            self.read_thread.start()
            
            print(f"终端监控已启动，进程 PID: {self.process.pid}")
            return True
            
        except Exception as e:
            print(f"启动终端监控失败: {e}")
            return False
    
    def _read_output(self):
        """读取进程输出（在后台线程中运行）"""
        try:
            for line in self.process.stdout:
                if not self.is_running:
                    break
                    
                line = line.rstrip('\n')
                
                # 添加到缓冲区
                with self.buffer_lock:
                    self.output_buffer.append(line)
                
                # 调用输出回调
                if self.on_output_callback:
                    self.on_output_callback(line)
                
                # 检测权限询问
                permission_detected = False
                permission_prompt = None
                
                # 使用权限检测器（如果可用）
                if self.permission_detector:
                    permission_prompt = self.permission_detector.detect(line)
                    if permission_prompt:
                        permission_detected = True
                else:
                    # 回退到简单检测
                    if self._is_permission_prompt(line):
                        permission_detected = True
                
                # 处理权限检测
                if permission_detected:
                    if self.on_permission_callback:
                        self.on_permission_callback(line, permission_prompt)
                    
                    # 自动回复（如果启用）
                    if self.auto_response_enabled and permission_prompt:
                        self._handle_auto_response(permission_prompt)
                    
        except Exception as e:
            print(f"读取输出时出错: {e}")
    
    def _is_permission_prompt(self, line: str) -> bool:
        """检测是否为权限询问（简单版本）"""
        permission_patterns = [
            r'Apply these changes\?',
            r'Create new file\?',
            r'Run shell command\?',
            r'\(Y\)es/\(N\)o',
            r'Add file to the chat\?',
            r'Create new file\?.*\[Yes\]:',
            r'\[Y\]es/\[N\]o',
            r'Do you want to.*\?',
            r'Shall I.*\?',
            r'Permission to.*\?',
        ]
        
        line_lower = line.lower()
        for pattern in permission_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False
    
    def _handle_auto_response(self, permission_prompt) -> bool:
        """处理自动回复"""
        if not self.auto_response_enabled or not self.process:
            return False
        
        try:
            # 获取决策
            should_allow = self._should_auto_allow(permission_prompt)
            
            # 根据决策获取响应
            if should_allow:
                response = self.auto_response_config.get("allow_response", "y")
            else:
                response = self.auto_response_config.get("deny_response", "n")
            
            # 添加延迟（如果需要）
            delay = self.auto_response_config.get("delay", 0)
            if delay > 0:
                import time
                time.sleep(delay)
            
            # 发送响应
            if self.send_input(response):
                # 记录日志
                permission_type = "未知"
                if hasattr(permission_prompt, 'permission_type'):
                    permission_type = permission_prompt.permission_type.value
                
                files_info = ""
                if hasattr(permission_prompt, 'files') and permission_prompt.files:
                    files_info = f", 文件: {', '.join(permission_prompt.files[:3])}"
                    if len(permission_prompt.files) > 3:
                        files_info += f" 等{len(permission_prompt.files)}个文件"
                
                print(f"[终端监控] 自动回复: '{response}' (类型: {permission_type}{files_info}, 允许: {should_allow})")
                return True
            else:
                print(f"[终端监控] 自动回复失败")
                return False
                
        except Exception as e:
            print(f"[终端监控] 自动回复出错: {e}")
            return False
    
    def _should_auto_allow(self, permission_prompt) -> bool:
        """检查是否应该自动允许权限请求"""
        if not self.auto_response_config:
            return True
        
        # 如果有权限检测器，使用它提取文件信息
        files = []
        if hasattr(permission_prompt, 'files'):
            files = permission_prompt.files
        elif hasattr(permission_prompt, 'metadata') and 'files' in permission_prompt.metadata:
            files = permission_prompt.metadata['files']
        
        # 检查白名单
        whitelist = self.auto_response_config.get("whitelist", [])
        if whitelist and files:
            for file in files:
                for pattern in whitelist:
                    if re.match(pattern, file):
                        return True
        
        # 检查黑名单
        blacklist = self.auto_response_config.get("blacklist", [])
        if blacklist and files:
            for file in files:
                for pattern in blacklist:
                    if re.match(pattern, file):
                        return False
        
        # 默认根据配置决定
        return self.auto_response_config.get("default_allow", True)
    
    def check(self) -> Dict[str, Any]:
        """
        检查状态
        
        Returns:
            dict: 状态信息 {
                "status": "working" | "completed" | "error" | "idle",
                "output": "捕获的输出内容",
                "metadata": {
                    "process_alive": bool,
                    "buffer_size": int,
                    "command": str
                }
            }
        """
        if not self.is_running:
            return {
                "status": "error",
                "output": "",
                "metadata": {"error": "监控未启动"}
            }
        
        try:
            # 检查进程状态
            if self.process is None:
                return {
                    "status": "error",
                    "output": "",
                    "metadata": {"error": "进程未启动"}
                }
            
            # 获取进程状态
            return_code = self.process.poll()
            process_alive = return_code is None
            
            # 获取缓冲区的输出
            with self.buffer_lock:
                output_lines = self.output_buffer.copy()
                self.output_buffer.clear()
            
            output = "\n".join(output_lines)
            
            # 确定状态
            if not process_alive:
                status = "completed" if return_code == 0 else "error"
            elif output_lines:
                status = "working"
            else:
                status = "idle"
            
            return {
                "status": status,
                "output": output,
                "metadata": {
                    "process_alive": process_alive,
                    "return_code": return_code,
                    "buffer_size": len(output_lines),
                    "command": " ".join(self.command) if self.command else "",
                    "project_path": self.project_path
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "metadata": {"error": str(e)}
            }
    
    def stop(self):
        """停止监控"""
        self.is_running = False
        
        if self.process:
            try:
                # 尝试优雅终止
                self.process.terminate()
                time.sleep(0.5)
                
                # 如果还在运行，强制终止
                if self.process.poll() is None:
                    self.process.kill()
                    
                self.process.wait(timeout=2)
            except:
                pass
            
            self.process = None
        
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=1)
        
        print(f"终端监控已停止")
    
    def send_input(self, text: str) -> bool:
        """
        发送输入到进程（如 'y' 或 'n'）
        
        Args:
            text: 要发送的文本
            
        Returns:
            bool: 是否成功发送
        """
        if not self.process or not self.process.stdin:
            return False
        
        try:
            self.process.stdin.write(text + '\n')
            self.process.stdin.flush()
            return True
        except:
            return False
    
    def is_process_alive(self) -> bool:
        """检查进程是否仍在运行"""
        if not self.process:
            return False
        return self.process.poll() is None