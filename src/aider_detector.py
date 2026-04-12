# -*- coding: utf-8 -*-
"""
Aider 配置自动检测模块
自动发现 Aider 日志文件路径和配置
"""

import os
import glob
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from .utils import expand_path


class AiderConfigDetector:
    """Aider 配置自动检测器"""
    
    # Aider 可能的日志文件名（按优先级排序）
    LOG_FILE_PATTERNS = [
        ".aider.chat.history.md",  # 新版本默认（隐藏文件）
        ".aider.history",          # 旧版本默认（隐藏文件）
        "chat.history.md",         # 新版本默认
        "history",                 # 旧版本默认
        "*.history.md",            # 带时间戳的版本
        "*.history",               # 带时间戳的版本
        "*.log",                   # 通用日志
        "*.txt",                   # 文本文件
    ]
    
    # Aider 配置文件路径
    CONFIG_PATHS = [
        "~/.aider.conf",
        "~/.config/aider.conf",
        "~/.aider/config.json",
    ]
    
    # Aider 特征关键词
    AIDER_KEYWORDS = [
        "Added",           # 添加文件到对话
        "Committed",       # 提交更改
        "> ",              # 提示符（用户输入）
        "aider",           # Aider 名称
        "chat",            # 聊天
        "history",         # 历史
        "I'll help you",   # Aider 响应
        "修改了",           # 中文：修改了
        "创建了",           # 中文：创建了
    ]
    
    def __init__(self):
        self.aider_dir = expand_path("~/.aider")
        self.found_logs: List[str] = []
        self.found_configs: List[str] = []
        
    def discover_log_files(self) -> List[str]:
        """
        发现 Aider 日志文件
        
        Returns:
            找到的日志文件路径列表
        """
        home_dir = expand_path("~")
        
        # 搜索位置：Aider 目录和用户主目录
        search_dirs = []
        if os.path.exists(self.aider_dir):
            search_dirs.append(self.aider_dir)
        search_dirs.append(home_dir)
        
        print(f"搜索 Aider 日志文件...")
        
        # 按模式搜索所有目录
        for search_dir in search_dirs:
            for pattern in self.LOG_FILE_PATTERNS:
                pattern_path = os.path.join(search_dir, pattern)
                matches = glob.glob(pattern_path, recursive=True)
                
                for match in matches:
                    if os.path.isfile(match) and self._is_aider_log_file(match):
                        if match not in self.found_logs:
                            self.found_logs.append(match)
                            print(f"  Found Aider log: {match}")
        
        # 如果没有找到，搜索子目录
        if not self.found_logs:
            for root, dirs, files in os.walk(self.aider_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self._is_aider_log_file(file_path):
                        if file_path not in self.found_logs:
                            self.found_logs.append(file_path)
                            print(f"  在子目录找到 Aider 日志文件: {file_path}")
        
        # 按修改时间排序，最新的在前
        self.found_logs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        return self.found_logs
    
    def discover_config_files(self) -> List[str]:
        """
        发现 Aider 配置文件
        
        Returns:
            找到的配置文件路径列表
        """
        for config_path in self.CONFIG_PATHS:
            expanded_path = expand_path(config_path)
            if os.path.exists(expanded_path):
                self.found_configs.append(expanded_path)
                print(f"找到 Aider 配置文件: {expanded_path}")
        
        return self.found_configs
    
    def _is_aider_log_file(self, file_path: str) -> bool:
        """
        判断文件是否为 Aider 日志文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为 Aider 日志文件
        """
        try:
            # 检查文件大小（避免读取大文件）
            if os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10MB
                return False
            
            # 检查文件扩展名
            filename = os.path.basename(file_path).lower()
            if "history" in filename or "chat" in filename:
                return True
            
            # 读取文件开头部分检查特征
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(4096)  # 读取前4KB
                
                # 检查是否包含特征关键词
                keyword_count = 0
                for keyword in self.AIDER_KEYWORDS:
                    if keyword in content:
                        keyword_count += 1
                
                # 如果有足够多的特征关键词，认为是 Aider 日志
                if keyword_count >= 2:
                    return True
            
            return False
            
        except (IOError, UnicodeDecodeError, OSError):
            return False
    
    def get_log_file_config(self) -> Dict[str, Any]:
        """
        从日志文件推断配置
        
        Returns:
            配置字典
        """
        config = {
            "log_path": None,
            "completion_markers": [
                "Added",
                "Committed",
                "^>"  # 正则：以 > 开头的行（提示符）
            ],
            "auto_detected": True
        }
        
        # 获取日志文件
        log_files = self.discover_log_files()
        
        if not log_files:
            print("警告: 未找到 Aider 日志文件")
            # 使用默认路径
            default_path = os.path.join(self.aider_dir, "chat.history.md")
            config["log_path"] = default_path
            config["auto_detected"] = False
            print(f"使用默认日志路径: {default_path}")
            return config
        
        # 优先选择常见的文件名
        preferred_names = ["chat.history.md", "history"]
        
        for preferred in preferred_names:
            for log_file in log_files:
                if os.path.basename(log_file) == preferred:
                    config["log_path"] = log_file
                    print(f"选择首选日志文件: {log_file}")
                    return config
        
        # 如果没有首选文件，选择最新的
        latest_log = log_files[0]
        config["log_path"] = latest_log
        print(f"选择最新日志文件: {latest_log}")
        
        return config
    
    def get_aider_version(self) -> Optional[str]:
        """
        尝试获取 Aider 版本信息
        
        Returns:
            Aider 版本号，如果获取不到返回 None
        """
        # 检查配置文件
        configs = self.discover_config_files()
        
        for config_file in configs:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    if config_file.endswith('.json'):
                        config = json.load(f)
                        if 'version' in config:
                            return config['version']
                    else:
                        # 简单文本配置
                        content = f.read()
                        if 'version' in content:
                            # 简单提取版本号
                            import re
                            match = re.search(r'version[\s:=]+([\d.]+)', content)
                            if match:
                                return match.group(1)
            except (IOError, json.JSONDecodeError):
                continue
        
        return None
    
    def analyze_log_patterns(self, log_file: str) -> Dict[str, Any]:
        """
        分析日志文件模式
        
        Args:
            log_file: 日志文件路径
            
        Returns:
            分析结果
        """
        result = {
            "has_added": False,
            "has_committed": False,
            "has_prompt": False,
            "line_count": 0,
            "encoding": "unknown"
        }
        
        try:
            # 尝试不同编码
            encodings = ['utf-8', 'gbk', 'latin-1']
            
            for encoding in encodings:
                try:
                    with open(log_file, 'r', encoding=encoding) as f:
                        lines = f.readlines()
                        result["line_count"] = len(lines)
                        result["encoding"] = encoding
                        
                        # 分析内容
                        content = ''.join(lines[:100])  # 前100行
                        result["has_added"] = "Added" in content
                        result["has_committed"] = "Committed" in content
                        result["has_prompt"] = "> " in content
                        
                        print(f"  日志分析: {len(lines)} 行, 编码: {encoding}")
                        print(f"    包含 Added: {result['has_added']}")
                        print(f"    包含 Committed: {result['has_committed']}")
                        print(f"    包含提示符: {result['has_prompt']}")
                        
                        break
                except UnicodeDecodeError:
                    continue
                    
        except IOError:
            pass
        
        return result


def auto_detect_aider_config() -> Dict[str, Any]:
    """
    自动检测 Aider 配置（便捷函数）
    
    Returns:
        Aider 配置字典
    """
    detector = AiderConfigDetector()
    return detector.get_log_file_config()


def validate_aider_log_path(log_path: str) -> bool:
    """
    验证 Aider 日志路径是否有效
    
    Args:
        log_path: 日志文件路径
        
    Returns:
        是否有效
    """
    if not os.path.exists(log_path):
        print(f"日志文件不存在: {log_path}")
        return False
    
    detector = AiderConfigDetector()
    return detector._is_aider_log_file(log_path)


if __name__ == "__main__":
    # 测试代码
    print("测试 Aider 配置自动检测...")
    detector = AiderConfigDetector()
    
    # 发现日志文件
    log_files = detector.discover_log_files()
    print(f"\n找到 {len(log_files)} 个日志文件:")
    for log_file in log_files:
        print(f"  - {log_file}")
    
    # 获取配置
    config = detector.get_log_file_config()
    print(f"\n自动检测的配置:")
    print(f"  日志路径: {config['log_path']}")
    print(f"  自动检测: {config['auto_detected']}")
    
    # 分析日志文件
    if config['log_path'] and os.path.exists(config['log_path']):
        print(f"\n分析日志文件:")
        analysis = detector.analyze_log_patterns(config['log_path'])
        print(f"  分析结果: {analysis}")