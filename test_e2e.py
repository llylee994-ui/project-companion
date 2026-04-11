#!/usr/bin/env python3
"""
端到端测试 - 模拟完整的 Aider 工作流程
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


def simulate_aider_workflow():
    """模拟 Aider 工作流程"""
    print("=" * 60)
    print("模拟 Aider 工作流程测试")
    print("=" * 60)
    
    # 创建临时日志文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
        log_file = f.name
        print(f"创建临时日志文件: {log_file}")
    
    try:
        # 1. 初始化监控器
        print("\n1. 初始化监控器...")
        monitor = LogFileMonitor()
        if not monitor.start({"log_path": log_file}):
            print("错误: 监控器启动失败")
            return 1
        
        # 2. 初始化检测器
        print("2. 初始化检测器...")
        detector = CompletionDetector(["Added", "Committed", "^>"])
        detector.start_session()
        
        # 3. 初始化通知器
        print("3. 初始化通知器...")
        notifier = Notifier([{"type": "feishu", "target": "test_chat"}])
        
        # 4. 模拟 Aider 工作流程
        print("\n4. 模拟 Aider 工作流程:")
        
        # 步骤 1: 用户输入
        print("   步骤 1: 用户输入请求")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("> 帮我修复这个bug\n")
        time.sleep(0.5)
        
        # 检查
        result = monitor.check()
        if result["status"] == "working":
            detection = detector.feed(result["output"])
            print(f"   检测结果: {'完成' if detection['completed'] else '进行中'}")
        
        # 步骤 2: Aider 响应
        print("   步骤 2: Aider 分析问题")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("我来帮你修复这个bug...\n")
            f.write("分析代码中...\n")
        time.sleep(0.5)
        
        result = monitor.check()
        if result["status"] == "working":
            detection = detector.feed(result["output"])
            print(f"   检测结果: {'完成' if detection['completed'] else '进行中'}")
        
        # 步骤 3: Aider 修改文件
        print("   步骤 3: Aider 修改文件")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("修改了 src/app.py\n")
            f.write("修改了 src/utils.py\n")
        time.sleep(0.5)
        
        result = monitor.check()
        if result["status"] == "working":
            detection = detector.feed(result["output"])
            print(f"   检测结果: {'完成' if detection['completed'] else '进行中'}")
        
        # 步骤 4: Aider 添加文件到对话
        print("   步骤 4: Aider 添加文件到对话")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("Added src/app.py to the chat\n")
        time.sleep(0.5)
        
        result = monitor.check()
        if result["status"] == "working":
            detection = detector.feed(result["output"])
            if detection["completed"]:
                print(f"   检测到完成! 标记: {detection['matched_marker']}")
                print(f"   耗时: {detection['duration']}")
                print(f"   摘要: {detection['summary']}")
                
                # 发送通知
                notify_result = notifier.send_aider_completion(
                    project_name="测试项目",
                    duration=detection["duration"],
                    summary=detection["summary"]
                )
                print(f"   通知结果: {notify_result}")
            else:
                print(f"   检测结果: 进行中")
        
        # 步骤 5: Aider 提交更改
        print("   步骤 5: Aider 提交更改")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("Committed the changes\n")
        time.sleep(0.5)
        
        result = monitor.check()
        if result["status"] == "working":
            detection = detector.feed(result["output"])
            if detection["completed"]:
                print(f"   检测到完成! 标记: {detection['matched_marker']}")
        
        # 步骤 6: 返回提示符
        print("   步骤 6: 返回提示符")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("> \n")
        time.sleep(0.5)
        
        result = monitor.check()
        if result["status"] == "working":
            detection = detector.feed(result["output"])
            if detection["completed"]:
                print(f"   检测到完成! 标记: {detection['matched_marker']}")
        
        # 5. 清理
        print("\n5. 清理资源...")
        monitor.stop()
        
        print("\n" + "=" * 60)
        print("端到端测试完成!")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # 清理临时文件
        if os.path.exists(log_file):
            os.unlink(log_file)
            print(f"已删除临时文件: {log_file}")


def test_config_loading():
    """测试配置加载"""
    print("\n" + "=" * 60)
    print("测试配置加载")
    print("=" * 60)
    
    # 创建临时配置文件
    config_content = """version: "1.0"

projects:
  - name: "test-project"
    path: "~/projects/test"
    tool: "aider"
    enabled: true
    aider_config:
      log_path: "~/.aider/history"
      completion_markers:
        - "Added"
        - "Committed"
        - "^>"

notification:
  enabled: true
  channels:
    - type: "feishu"
      target: "chat:test"

monitoring:
  check_interval: 2
  max_session_duration: 1800
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        config_file = f.name
        f.write(config_content)
    
    try:
        # 测试配置加载
        from src.utils import load_config
        config = load_config(config_file)
        
        if config:
            print("配置加载成功!")
            print(f"版本: {config.get('version')}")
            print(f"项目数: {len(config.get('projects', []))}")
            print(f"通知启用: {config.get('notification', {}).get('enabled')}")
            print(f"检查间隔: {config.get('monitoring', {}).get('check_interval')}秒")
        else:
            print("配置加载失败")
            
    except Exception as e:
        print(f"配置加载测试失败: {e}")
        
    finally:
        if os.path.exists(config_file):
            os.unlink(config_file)
    
    print("配置加载测试完成!")


def main():
    """运行所有测试"""
    print("AI Coding Companion 端到端测试")
    print("=" * 60)
    
    # 运行端到端测试
    result1 = simulate_aider_workflow()
    
    # 运行配置加载测试
    result2 = test_config_loading()
    
    print("\n" + "=" * 60)
    if result1 == 0:
        print("所有测试通过!")
    else:
        print("测试失败!")
    print("=" * 60)
    
    return result1


if __name__ == "__main__":
    sys.exit(main())