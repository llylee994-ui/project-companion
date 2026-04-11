#!/usr/bin/env python3
"""
测试 Aider 监控功能
"""

import os
import sys
import tempfile
import time

# 添加 src 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.strategies.log_monitor import LogFileMonitor
from src.detector import CompletionDetector
from src.notifier import Notifier


def test_log_monitor():
    """测试日志监控器"""
    print("测试 LogFileMonitor...")
    
    # 创建临时日志文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        log_file = f.name
        f.write("初始内容\n")
    
    try:
        # 创建监控器
        monitor = LogFileMonitor()
        
        # 启动监控
        success = monitor.start({"log_path": log_file})
        assert success, "监控器启动失败"
        print("[OK] 监控器启动成功")
        
        # 检查初始状态
        result = monitor.check()
        assert result["status"] == "idle", f"预期状态为 idle，实际为 {result['status']}"
        print("[OK] 初始检查正确")
        
        # 写入新内容
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("新内容：Aider 正在工作...\n")
        
        # 再次检查
        result = monitor.check()
        assert result["status"] == "working", f"预期状态为 working，实际为 {result['status']}"
        assert "新内容" in result["output"], "未读取到新内容"
        print("[OK] 成功读取新内容")
        
        # 测试完成检测
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("Added src/file.py to the chat\n")
        
        result = monitor.check_completion(["Added"])
        assert result["completed"], "应检测到完成标记"
        assert result["matched_marker"] == "Added", f"匹配标记应为 Added，实际为 {result['matched_marker']}"
        print("✓ 成功检测到完成标记 'Added'")
        
        monitor.stop()
        print("✓ 监控器停止成功")
        
    finally:
        # 清理临时文件
        if os.path.exists(log_file):
            os.unlink(log_file)
    
    print("LogFileMonitor 测试通过！\n")


def test_completion_detector():
    """测试完成检测器"""
    print("测试 CompletionDetector...")
    
    # 创建检测器
    detector = CompletionDetector(["Added", "Committed", "^>"])
    
    # 开始会话
    detector.start_session()
    print("✓ 会话开始")
    
    # 测试未完成状态
    result = detector.feed("Aider 正在工作...")
    assert not result["completed"], "不应检测为完成"
    print("✓ 未完成状态检测正确")
    
    # 测试完成检测
    result = detector.feed("Added src/file.py to the chat")
    assert result["completed"], "应检测为完成"
    assert result["matched_marker"] == "Added", f"匹配标记应为 Added，实际为 {result['matched_marker']}"
    assert result["duration"] is not None, "时长不应为 None"
    print("✓ 完成状态检测正确")
    print(f"  耗时: {result['duration']}")
    print(f"  摘要: {result['summary']}")
    
    # 测试正则表达式匹配
    detector2 = CompletionDetector(["^>"])
    detector2.start_session()
    result = detector2.feed("用户输入\n> ")
    assert result["completed"], "应检测到提示符完成"
    print("✓ 正则表达式匹配正确")
    
    print("CompletionDetector 测试通过！\n")


def test_notifier():
    """测试通知器"""
    print("测试 Notifier...")
    
    # 创建通知器
    channels = [
        {"type": "feishu", "target": "test_chat"}
    ]
    notifier = Notifier(channels)
    
    # 测试普通消息
    results = notifier.send("测试消息", "测试标题")
    assert "feishu" in results, "应包含飞书通知结果"
    assert results["feishu"], "飞书通知应成功"
    print("✓ 普通消息发送测试通过")
    
    # 测试 Aider 完成消息
    results = notifier.send_aider_completion(
        project_name="测试项目",
        duration="5分30秒",
        summary="修复了bug\n添加了新功能"
    )
    assert results["feishu"], "Aider 完成通知应成功"
    print("✓ Aider 完成消息发送测试通过")
    
    print("Notifier 测试通过！\n")


def test_integration():
    """测试集成功能"""
    print("测试集成功能...")
    
    # 创建临时日志文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        log_file = f.name
    
    try:
        # 模拟 Aider 工作流程
        monitor = LogFileMonitor()
        monitor.start({"log_path": log_file})
        
        detector = CompletionDetector(["Added", "Committed", "^>"])
        detector.start_session()
        
        notifier = Notifier([{"type": "feishu", "target": "test"}])
        
        # 模拟 Aider 工作
        steps = [
            "用户: 帮我修复这个bug",
            "Aider: 我来帮你修复...",
            "修改了 src/file.py",
            "Added src/file.py to the chat",
            "Committed the changes",
            "> "
        ]
        
        for step in steps:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(step + "\n")
            
            time.sleep(0.1)  # 短暂等待
            
            # 检查新内容
            result = monitor.check()
            if result["status"] == "working" and result["output"]:
                detection = detector.feed(result["output"])
                
                if detection["completed"]:
                    print(f"✓ 检测到完成！标记: {detection['matched_marker']}")
                    print(f"  耗时: {detection['duration']}")
                    print(f"  摘要: {detection['summary']}")
                    
                    # 发送通知
                    notify_result = notifier.send_aider_completion(
                        project_name="集成测试项目",
                        duration=detection["duration"],
                        summary=detection["summary"]
                    )
                    print(f"  通知结果: {notify_result}")
                    break
        
        monitor.stop()
        
    finally:
        if os.path.exists(log_file):
            os.unlink(log_file)
    
    print("集成测试通过！\n")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("AI Coding Companion 功能测试")
    print("=" * 60)
    
    try:
        test_log_monitor()
        test_completion_detector()
        test_notifier()
        test_integration()
        
        print("=" * 60)
        print("所有测试通过！✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())