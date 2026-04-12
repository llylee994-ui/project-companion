# -*- coding: utf-8 -*-
"""
日志文件监控策略 - 用于 Aider
"""

import os
import time
from typing import Dict, Any, List
from .base import MonitorStrategy


class LogFileMonitor(MonitorStrategy):
    """日志文件监控 - 用于 Aider"""
    
    def __init__(self):
        self.log_path = None
        self.last_position = 0
        self.last_modified = 0
        self.is_running = False
        
    def get_name(self) -> str:
        return "log_file_monitor"
    
    def start(self, config: Dict[str, Any]) -> bool:
        """
        启动日志文件监控
        
        Args:
            config: 配置字典，必须包含 "log_path"
            
        Returns:
            bool: 是否成功启动
        """
        try:
            self.log_path = os.path.expanduser(config.get("log_path", ""))
            if not self.log_path:
                print(f"错误: 未指定日志路径")
                return False
                
            # 检查文件是否存在
            if not os.path.exists(self.log_path):
                print(f"警告: 日志文件不存在: {self.log_path}")
                print(f"等待文件创建...")
                # 文件不存在时仍然启动，等待文件创建
                self.last_position = 0
            else:
                # 记录当前文件位置
                with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0, 2)  # 跳到文件末尾
                    self.last_position = f.tell()
            
            self.is_running = True
            print(f"开始监控日志文件: {self.log_path}")
            return True
            
        except Exception as e:
            print(f"启动日志监控失败: {e}")
            return False
    
    def check(self) -> Dict[str, Any]:
        """
        检查日志文件的新内容
        
        Returns:
            dict: 状态信息 {
                "status": "working" | "completed" | "error" | "idle",
                "output": "新增内容",
                "metadata": {
                    "file_path": str,
                    "new_content_size": int
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
            # 检查文件是否存在
            if not os.path.exists(self.log_path):
                return {
                    "status": "idle",
                    "output": "",
                    "metadata": {"file_exists": False}
                }
            
            # 检查文件大小
            current_size = os.path.getsize(self.log_path)
            
            # 如果文件被截断或重建，重置位置
            if current_size < self.last_position:
                print(f"日志文件被重置，重置读取位置")
                self.last_position = 0
            
            # 如果没有新内容
            if current_size <= self.last_position:
                return {
                    "status": "idle",
                    "output": "",
                    "metadata": {"new_content_size": 0}
                }
            
            # 读取新增内容
            with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(self.last_position)
                new_content = f.read()
                self.last_position = f.tell()
            
            # 更新最后修改时间
            self.last_modified = os.path.getmtime(self.log_path)
            
            return {
                "status": "working",
                "output": new_content,
                "metadata": {
                    "file_path": self.log_path,
                    "new_content_size": len(new_content),
                    "total_size": current_size
                }
            }
            
        except PermissionError:
            return {
                "status": "error",
                "output": "",
                "metadata": {"error": "权限不足，无法读取日志文件"}
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
        print(f"停止监控日志文件: {self.log_path}")
    
    def check_completion(self, markers: List[str]) -> Dict[str, Any]:
        """
        检查是否包含完成标记（兼容旧接口）
        
        Args:
            markers: 完成标记列表
            
        Returns:
            dict: 完成检测结果 {
                "completed": bool,
                "output": str,
                "matched_marker": str or None
            }
        """
        result = self.check()
        
        if result["status"] != "working" or not result["output"]:
            return {
                "completed": False,
                "output": "",
                "matched_marker": None
            }
        
        new_content = result["output"]
        
        # 检查所有标记
        for marker in markers:
            if marker in new_content:
                return {
                    "completed": True,
                    "output": new_content,
                    "matched_marker": marker
                }
        
        return {
            "completed": False,
            "output": new_content,
            "matched_marker": None
        }
    
    def read_new_content(self) -> str:
        """
        读取新增内容（兼容旧接口）
        
        Returns:
            str: 新增内容
        """
        result = self.check()
        return result["output"] if result["status"] == "working" else ""