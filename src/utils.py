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


def ensure_dir(path: str) -> Path:
    """
    确保目录存在，不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        Path 对象
    """
    p = Path(path).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return p
