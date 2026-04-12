# -*- coding: utf-8 -*-
"""
工具函数模块
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def load_config(config_path: str = "config.yaml") -> Optional[Dict[str, Any]]:
    """
    加载 YAML 配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典，失败返回 None
    """
    path = Path(config_path).expanduser()
    
    if not path.exists():
        print(f"配置文件不存在: {path}")
        return None
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"配置文件解析错误: {e}")
        return None
    except IOError as e:
        print(f"读取配置文件失败: {e}")
        return None


def expand_path(path: str) -> str:
    """
    展开路径中的 ~ 和环境变量
    
    Args:
        path: 原始路径
        
    Returns:
        展开后的绝对路径
    """
    expanded = os.path.expanduser(os.path.expandvars(path))
    return os.path.abspath(expanded)


def format_duration(seconds: int) -> str:
    """
    格式化秒数为易读形式
    
    Args:
        seconds: 秒数
        
    Returns:
        如 "2小时30分钟"
    """
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}分钟"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes == 0:
            return f"{hours}小时"
        return f"{hours}小时{minutes}分钟"


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断字符串
    
    Args:
        s: 原始字符串
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        截断后的字符串
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def find_aider_log() -> Optional[str]:
    """
    自动查找 Aider 日志文件路径
    
    Returns:
        日志文件路径，找不到返回 None
    """
    home = Path.home()
    
    # 可能的日志路径（按优先级）
    possible_paths = [
        home / ".aider.chat.history.md",
        home / ".aider" / "history",
        home / ".aider" / "aider.chat.history.md",
        home / ".config" / "aider" / "history",
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    # 如果没找到，返回最可能的路径（让程序创建）
    return str(home / ".aider.chat.history.md")


def auto_detect_tool_config(tool_type: str) -> Dict[str, Any]:
    """
    自动检测工具配置
    
    Args:
        tool_type: 工具类型 (aider, claude, codex)
        
    Returns:
        自动检测的配置字典
    """
    if tool_type == "aider":
        # 使用新的检测器
        try:
            from .aider_detector import auto_detect_aider_config
            return auto_detect_aider_config()
        except ImportError:
            # 回退到简单检测
            log_path = find_aider_log()
            return {
                "log_path": log_path,
                "completion_markers": ["Added", "Committed", "^>"],
                "auto_detected": False
            }
    
    # 其他工具的默认配置
    return {}


# 添加到现有函数后面
