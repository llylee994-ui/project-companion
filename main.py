#!/usr/bin/env python3
"""
Project Companion - 主入口
OpenClaw Skill 执行时调用
"""

import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.watcher import watch_projects
from src.summarizer import Summarizer
from src.notifier import Notifier
from src.utils import load_config, expand_path


def main():
    """主函数"""
    # 加载配置
    config = load_config("config.yaml")
    if not config:
        print("无法加载配置，退出")
        return 1
    
    projects = config.get("projects", [])
    notification_config = config.get("notification", {})
    summary_config = config.get("summary", {})
    
    if not projects:
        print("没有配置项目，退出")
        return 0
    
    # 检查项目变更
    print(f"正在检查 {len(projects)} 个项目...")
    changes = watch_projects(projects)
    
    if not changes:
        print("没有检测到新提交")
        return 0
    
    print(f"检测到 {len(changes)} 个项目有新提交")
    
    # 初始化总结器和通知器
    summarizer = Summarizer(
        mode=summary_config.get("mode", "brief"),
        include_ai=summary_config.get("include_ai", False)
    )
    
    notifier = Notifier(notification_config.get("channels", []))
    
    # 处理每个变更
    for change in changes:
        # 生成总结
        summary = summarizer.generate(change)
        
        print(f"\n{'='*50}")
        print(f"项目: {change['project_name']}")
        print(f"{'='*50}")
        print(summary)
        
        # 发送通知
        if notification_config.get("enabled", True):
            results = notifier.send(summary)
            print(f"\n通知发送结果: {results}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
