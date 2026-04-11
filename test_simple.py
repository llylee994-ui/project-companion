#!/usr/bin/env python3
"""
简单测试脚本 - 避免编码问题
"""

import os
import sys
import tempfile

# 添加 src 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.strategies.log_monitor import LogFileMonitor
from src.detector import CompletionDetector
from src.notifier import Notifier


def test_basic():
    """基本功能测试"""
    print("=" * 60)
    print("AI Coding Companion 基本功能测试")
    print("=" * 60)
    
    # 测试 1: LogFileMonitor
    print("\n1. 测试 LogFileMonitor...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        log_file = f.name
        f.write("初始内容\n")
    
    try:
        monitor = LogFileMonitor()
        success = monitor.start({"log_path": log_file})
        print(f"   启动结果: {'成功' if success else '失败'}")
        
        result = monitor.check()
        print(f"   初始检查状态: {result['status']}")
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("新内容\n")
        
        result = monitor.check()
        print(f"   新内容检查状态: {result['status']}")
        print(f"   新内容大小: {len(result['output'])} 字符")
        
        monitor.stop()
        print("   LogFileMonitor 测试完成")
        
    finally:
        if os.path.exists(log_file):
            os.unlink(log_file)
    
    # 测试 2: CompletionDetector
    print("\n2. 测试 CompletionDetector...")
    detector = CompletionDetector(["Added", "Committed", "^>"])
    detector.start_session()
    
    result = detector.feed("一些工作内容")
    print(f"   未完成检测: {'未完成' if not result['completed'] else '完成'}")
    
    result = detector.feed("Added file.py")
    print(f"   完成检测: {'完成' if result['completed'] else '未完成'}")
    if result['completed']:
        print(f"   匹配标记: {result['matched_marker']}")
        print(f"   耗时: {result['duration']}")
        print(f"   摘要: {result['summary']}")
    
    print("   CompletionDetector 测试完成")
    
    # 测试 3: Notifier
    print("\n3. 测试 Notifier...")
    notifier = Notifier([{"type": "feishu", "target": "test_chat"}])
    
    results = notifier.send("测试消息", "测试标题")
    print(f"   通知发送结果: {results}")
    
    results = notifier.send_aider_completion(
        project_name="测试项目",
        duration="3分45秒",
        summary="修复了bug"
    )
    print(f"   Aider完成通知结果: {results}")
    
    print("   Notifier 测试完成")
    
    print("\n" + "=" * 60)
    print("所有基本功能测试完成！")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(test_basic())