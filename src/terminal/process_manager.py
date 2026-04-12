# -*- coding: utf-8 -*-
"""
AI 工具进程管理器
负责启动、监控和管理 AI 工具进程
"""

import subprocess
import threading
import os
import time
from typing import Dict, Any, List, Optional, Callable


class AIProcessManager:
    """AI 工具进程管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.callbacks: Dict[str, Callable] = {}
        self.read_threads: Dict[str, threading.Thread] = {}
        self.output_buffers: Dict[str, List[str]] = {}
        self.buffer_locks: Dict[str, threading.Lock] = {}
        
    def start_tool(self, tool_name: str, project_path: str, command: List[str] = None, 
                   env: Dict[str, str] = None) -> bool:
        """
        启动 AI 工具
        
        Args:
            tool_name: 工具名称（用于标识）
            project_path: 项目路径
            command: 启动命令（可选，默认根据工具名构建）
            env: 环境变量（可选）
            
        Returns:
            bool: 是否成功启动
        """
        try:
            # 构建命令
            if command is None:
                command = self._build_command(tool_name)
            
            if not command:
                print(f"错误: 无法为工具 '{tool_name}' 构建命令")
                return False
            
            # 准备环境变量
            env_vars = os.environ.copy()
            if env:
                env_vars.update(env)
            
            # 扩展项目路径
            expanded_path = os.path.expanduser(project_path)
            
            print(f"启动工具 '{tool_name}': {' '.join(command)}")
            print(f"项目路径: {expanded_path}")
            
            # 启动进程
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='ignore',
                cwd=expanded_path,
                env=env_vars
            )
            
            # 初始化数据结构
            self.processes[tool_name] = process
            self.output_buffers[tool_name] = []
            self.buffer_locks[tool_name] = threading.Lock()
            
            # 启动监控线程
            read_thread = threading.Thread(
                target=self._monitor_output,
                args=(tool_name, process),
                daemon=True
            )
            self.read_threads[tool_name] = read_thread
            read_thread.start()
            
            print(f"工具 '{tool_name}' 已启动，进程 PID: {process.pid}")
            return True
            
        except Exception as e:
            print(f"启动工具 '{tool_name}' 失败: {e}")
            return False
    
    def _build_command(self, tool_name: str) -> List[str]:
        """构建启动命令"""
        # 默认命令映射
        commands = {
            'aider': ['aider', '--model', 'deepseek-chat'],
            'claude': ['claude'],
            'codex': ['codex'],
        }
        
        # 从配置中获取命令（如果存在）
        if self.config and 'tools' in self.config:
            tool_config = self.config['tools'].get(tool_name, {})
            if 'command' in tool_config:
                cmd = tool_config['command']
                return [cmd] if isinstance(cmd, str) else cmd
        
        # 返回默认命令或工具名本身
        return commands.get(tool_name, [tool_name])
    
    def _monitor_output(self, tool_name: str, process: subprocess.Popen):
        """监控输出"""
        try:
            for line in process.stdout:
                line = line.rstrip('\n')
                
                # 添加到缓冲区
                with self.buffer_locks[tool_name]:
                    self.output_buffers[tool_name].append(line)
                
                # 调用回调
                if tool_name in self.callbacks:
                    self.callbacks[tool_name](line)
                    
        except Exception as e:
            print(f"监控工具 '{tool_name}' 输出时出错: {e}")
    
    def get_output(self, tool_name: str, clear: bool = True) -> List[str]:
        """
        获取工具输出
        
        Args:
            tool_name: 工具名称
            clear: 是否清空缓冲区
            
        Returns:
            List[str]: 输出行列表
        """
        if tool_name not in self.output_buffers:
            return []
        
        with self.buffer_locks[tool_name]:
            output = self.output_buffers[tool_name].copy()
            if clear:
                self.output_buffers[tool_name].clear()
        
        return output
    
    def send_response(self, tool_name: str, response: str) -> bool:
        """
        发送响应到工具（如 'y' 或 'n'）
        
        Args:
            tool_name: 工具名称
            response: 响应文本
            
        Returns:
            bool: 是否成功发送
        """
        process = self.processes.get(tool_name)
        if not process or not process.stdin:
            return False
        
        try:
            process.stdin.write(response + '\n')
            process.stdin.flush()
            return True
        except:
            return False
    
    def stop_tool(self, tool_name: str, timeout: float = 2.0) -> bool:
        """
        停止工具
        
        Args:
            tool_name: 工具名称
            timeout: 等待超时时间（秒）
            
        Returns:
            bool: 是否成功停止
        """
        process = self.processes.get(tool_name)
        if not process:
            return True
        
        try:
            # 尝试优雅终止
            process.terminate()
            time.sleep(0.5)
            
            # 如果还在运行，强制终止
            if process.poll() is None:
                process.kill()
            
            # 等待进程结束
            process.wait(timeout=timeout)
            
            # 清理资源
            if tool_name in self.processes:
                del self.processes[tool_name]
            if tool_name in self.output_buffers:
                del self.output_buffers[tool_name]
            if tool_name in self.buffer_locks:
                del self.buffer_locks[tool_name]
            if tool_name in self.callbacks:
                del self.callbacks[tool_name]
            
            print(f"工具 '{tool_name}' 已停止")
            return True
            
        except Exception as e:
            print(f"停止工具 '{tool_name}' 时出错: {e}")
            return False
    
    def is_tool_running(self, tool_name: str) -> bool:
        """检查工具是否在运行"""
        process = self.processes.get(tool_name)
        if not process:
            return False
        return process.poll() is None
    
    def register_callback(self, tool_name: str, callback: Callable):
        """注册输出回调函数"""
        self.callbacks[tool_name] = callback
    
    def get_running_tools(self) -> List[str]:
        """获取正在运行的工具列表"""
        return [name for name, process in self.processes.items() 
                if process.poll() is None]
    
    def stop_all(self, timeout: float = 3.0):
        """停止所有工具"""
        for tool_name in list(self.processes.keys()):
            self.stop_tool(tool_name, timeout)