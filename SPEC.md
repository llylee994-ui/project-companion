# AI Coding Companion Skill - 需求规格文档（最终版）

## 项目概述

一个通用的 OpenClaw Skill，用于监控 AI 编程工具的执行状态，在工具完成工作时主动通知用户。

**核心场景：**
```
用户: "帮我修这个 bug"
    ↓
AI 工具开始工作（可能需要几分钟）
    ↓
用户去干别的（刷手机、看文档、休息）✓
    ↓
AI 完成 → OpenClaw 主动发飞书/邮件通知
    ↓
用户回来继续下一轮
```

## 开发路线

### Phase 1: MVP - Aider 支持（当前）
**目标：** 支持 Aider 桌面版，跑通完整流程
- 监控 Aider 日志文件
- 检测工作完成
- 发送飞书通知
- **预计 3-5 天**

### Phase 2: 扩展 - 多工具支持
**目标：** 支持 Claude Code、Codex 等终端工具
- 终端输出捕获
- 自动检测工具类型
- **预计 1 周**

### Phase 3: 完整 - 桌面版全覆盖
**目标：** 支持 Cursor 等纯桌面应用
- 屏幕 OCR 监控（兜底方案）
- 混合策略自动切换
- **预计 2 周**

## 技术架构（策略模式）

```
ai-coding-companion/
├── SKILL.md
├── config.yaml
├── main.py
├── src/
│   ├── __init__.py
│   ├── strategies/           # 监控策略（核心）
│   │   ├── __init__.py
│   │   ├── base.py          # 抽象基类
│   │   ├── log_monitor.py   # 日志监控（Aider）
│   │   ├── terminal_monitor.py  # 终端捕获（Claude Code）
│   │   └── ocr_monitor.py   # 屏幕 OCR（桌面版兜底）
│   │
│   ├── detector.py          # 完成检测器
│   ├── notifier.py          # 通知发送
│   ├── summarizer.py        # 总结生成
│   └── utils.py
└── tests/
```

### 策略模式设计

```python
# src/strategies/base.py
from abc import ABC, abstractmethod

class MonitorStrategy(ABC):
    """监控策略抽象基类"""
    
    @abstractmethod
    def start(self, config: dict) -> bool:
        """启动监控，返回是否成功"""
        pass
    
    @abstractmethod
    def check(self) -> dict:
        """
        检查状态
        Returns: {
            "status": "working" | "completed" | "error",
            "output": "捕获的输出内容",
            "metadata": {}
        }
        """
        pass
    
    @abstractmethod
    def stop(self):
        """停止监控"""
        pass


# src/strategies/log_monitor.py
class LogFileMonitor(MonitorStrategy):
    """日志文件监控 - 用于 Aider"""
    
    def start(self, config):
        self.log_path = config["log_path"]
        self.last_position = 0
        # 打开文件，记录当前位置
        
    def check(self):
        # 读取新增内容
        # 检测完成标记
        pass


# src/strategies/terminal_monitor.py  
class TerminalMonitor(MonitorStrategy):
    """终端输出监控 - 用于 Claude Code"""
    # 实现终端捕获逻辑
    pass


# src/strategies/ocr_monitor.py
class ScreenOCRMonitor(MonitorStrategy):
    """屏幕 OCR 监控 - 桌面版兜底"""
    # 实现 OCR 逻辑
    pass
```

## Phase 1 MVP 详细需求（Aider 支持）

### 功能要求

1. **日志监控**
   - 监控 Aider 的日志文件（默认 `~/.aider/history`）
   - 实时读取新增内容
   - 支持自定义日志路径

2. **完成检测**
   - 检测 Aider 完成标记：
     - `"Added"` - 文件已添加
     - `"Committed"` - 已提交
     - 返回命令提示符（新行以 `$` 或 `>` 开头）
   - 过滤用户自己的输入

3. **通知发送**
   - 完成时发送飞书通知
   - 包含：工具名称、耗时、简要总结

4. **配置管理**
   - 支持多个 Aider 项目
   - 每个项目独立配置

### Aider 日志分析

Aider 日志格式示例：
```
# 用户输入
> 帮我修复这个 bug

# AI 思考过程
I'll help you fix this bug...

# 文件操作
Added src/fix.py to the chat

# Git 操作
Committed the changes

# 完成，返回提示符
> 
```

**检测逻辑：**
- 监控文件变化
- 读取新增行
- 检测 `"Added"`、`"Committed"`、返回提示符
- 提示符出现 = 本次交互完成

### 配置示例

```yaml
# config.yaml
version: "1.0"

# 监控的项目
projects:
  - name: "my-web-app"
    path: "~/projects/my-web-app"
    tool: "aider"                    # 工具类型
    enabled: true
    
    # Aider 专用配置
    aider_config:
      log_path: "~/.aider/history"   # 日志路径
      completion_markers:            # 完成标记
        - "Added"
        - "Committed"
        - "^>"                      # 正则：提示符

# 通知设置
notification:
  enabled: true
  channels:
    - type: "feishu"
      target: "chat:oc_xxx"          # 飞书群ID
      
  # 通知内容
  template: |
    🤖 Aider 完成
    
    📁 项目：{project_name}
    ⏱️ 耗时：{duration}
    
    📋 工作内容：
    {summary}

# 监控设置
monitoring:
  check_interval: 2                  # 检查间隔（秒）
  max_session_duration: 1800         # 最大会话时长（30分钟）
```

### 通知消息格式

```
🤖 Aider 完成

📁 项目：my-web-app
⏱️ 耗时：5分32秒

📋 工作内容：
   - 修复了用户认证模块的 JWT 验证问题
   - 添加了错误处理逻辑
   - 修改了 2 个文件

[查看详情]
```

## 后续阶段规划

### Phase 2: 多工具支持

```yaml
projects:
  - name: "backend-api"
    path: "~/projects/backend-api"
    tool: "claude-code"              # 新增支持
    claude_config:
      terminal_title: "claude"       # 终端窗口标题
      completion_markers:
        - "✓"
        - "^\$"                     # 返回 bash 提示符
        
  - name: "frontend"
    path: "~/projects/frontend"
    tool: "codex"
    codex_config:
      process_name: "codex"
```

### Phase 3: 自动检测 + OCR 兜底

```yaml
projects:
  - name: "cursor-project"
    path: "~/projects/cursor-project"
    tool: "auto"                     # 自动检测
    
    # 自动检测失败时的兜底方案
    fallback:
      enabled: true
      type: "ocr"                    # 屏幕 OCR
      region: [0, 0, 1920, 1080]     # 监控区域
      check_interval: 1              # OCR 检查间隔（秒）
```

## 关键实现要点

### 1. 日志文件监控（MVP）

```python
import os
import time

class LogFileMonitor:
    def __init__(self, log_path):
        self.log_path = os.path.expanduser(log_path)
        self.last_position = 0
        self.last_modified = 0
        
    def start(self):
        """初始化，记录当前文件位置"""
        if os.path.exists(self.log_path):
            with open(self.log_path, 'r', encoding='utf-8') as f:
                f.seek(0, 2)  # 跳到文件末尾
                self.last_position = f.tell()
                
    def read_new_content(self) -> str:
        """读取新增内容"""
        if not os.path.exists(self.log_path):
            return ""
            
        current_size = os.path.getsize(self.log_path)
        if current_size < self.last_position:
            # 文件被截断或重建
            self.last_position = 0
            
        with open(self.log_path, 'r', encoding='utf-8') as f:
            f.seek(self.last_position)
            new_content = f.read()
            self.last_position = f.tell()
            
        return new_content
        
    def check_completion(self, markers: list) -> dict:
        """
        检查是否完成
        
        Returns:
            {
                "completed": True/False,
                "output": "新增内容",
                "matched_marker": "匹配到的标记"
            }
        """
        new_content = self.read_new_content()
        if not new_content:
            return {"completed": False, "output": ""}
            
        for marker in markers:
            if marker in new_content:
                return {
                    "completed": True,
                    "output": new_content,
                    "matched_marker": marker
                }
                
        return {"completed": False, "output": new_content}
```

### 2. 完成检测器

```python
import re
import time
from datetime import datetime

class CompletionDetector:
    def __init__(self, markers: list):
        """
        Args:
            markers: 完成标记列表，支持普通字符串和正则
        """
        self.markers = markers
        self.start_time = None
        self.buffer = []
        
    def start_session(self):
        """开始新会话"""
        self.start_time = datetime.now()
        self.buffer = []
        
    def feed(self, content: str) -> dict:
        """
        输入新内容，检测是否完成
        
        Returns:
            {
                "completed": True/False,
                "duration": "5分32秒",
                "summary": "工作内容摘要"
            }
        """
        self.buffer.append(content)
        
        # 检查所有标记
        combined = "".join(self.buffer[-20:])  # 最近20条
        
        for marker in self.markers:
            if marker.startswith("^"):
                # 正则匹配
                pattern = marker[1:]  # 去掉 ^
                if re.search(pattern, combined, re.MULTILINE):
                    return self._build_result()
            else:
                # 普通字符串匹配
                if marker in combined:
                    return self._build_result()
                    
        return {"completed": False}
        
    def _build_result(self) -> dict:
        """构建完成结果"""
        duration = datetime.now() - self.start_time if self.start_time else None
        
        return {
            "completed": True,
            "duration": self._format_duration(duration),
            "summary": self._generate_summary(),
            "full_output": "".join(self.buffer)
        }
        
    def _format_duration(self, delta) -> str:
        """格式化时长"""
        if not delta:
            return "未知"
        total_seconds = int(delta.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        if minutes > 0:
            return f"{minutes}分{seconds}秒"
        return f"{seconds}秒"
        
    def _generate_summary(self) -> str:
        """生成工作摘要（简单版）"""
        # MVP 版本：统计关键信息
        full_text = "".join(self.buffer)
        
        lines = []
        
        # 统计文件操作
        if "Added" in full_text:
            count = full_text.count("Added")
            lines.append(f"添加了 {count} 个文件到对话")
            
        if "Committed" in full_text:
            lines.append("提交了代码变更")
            
        return "\n".join(lines) if lines else "完成工作"
```

### 3. 主循环

```python
import time
from src.strategies.log_monitor import LogFileMonitor
from src.detector import CompletionDetector
from src.notifier import Notifier

def main_loop(project_config):
    """主监控循环"""
    
    # 初始化监控器
    monitor = LogFileMonitor(project_config["aider_config"]["log_path"])
    monitor.start()
    
    # 初始化检测器
    detector = CompletionDetector(
        project_config["aider_config"]["completion_markers"]
    )
    detector.start_session()
    
    # 初始化通知器
    notifier = Notifier(project_config["notification"]["channels"])
    
    print(f"开始监控项目: {project_config['name']}")
    
    try:
        while True:
            # 检查新内容
            result = monitor.check_completion(
                project_config["aider_config"]["completion_markers"]
            )
            
            if result["output"]:
                # 有新内容，喂给检测器
                detection = detector.feed(result["output"])
                
                if detection["completed"]:
                    print(f"检测到完成！耗时: {detection['duration']}")
                    
                    # 发送通知
                    notifier.send(
                        project=project_config["name"],
                        duration=detection["duration"],
                        summary=detection["summary"]
                    )
                    
                    # 重置，准备下一次
                    detector.start_session()
                    
            time.sleep(project_config["monitoring"]["check_interval"])
            
    except KeyboardInterrupt:
        print("监控已停止")
        monitor.stop()
```

## 注意事项

1. **文件编码**：Aider 日志通常是 UTF-8，但要处理编码错误
2. **文件锁**：日志文件可能被 Aider 占用，使用 `errors='ignore'`
3. **性能**：检查间隔不要太短（建议 2-5 秒）
4. **误报**：完成标记可能出现在对话中，需要上下文判断
5. **隐私**：日志可能包含敏感信息，不存储完整日志

## 测试计划

### 单元测试
- [ ] LogFileMonitor 读取文件
- [ ] CompletionDetector 标记检测
- [ ] Notifier 消息格式化

### 集成测试
- [ ] 完整流程：Aider 工作 → 检测完成 → 发送通知
- [ ] 多个项目同时监控
- [ ] 长时间运行稳定性

### 手动测试场景
1. 正常对话完成
2. Aider 修改多个文件
3. Aider 提交代码
4. 用户中途取消
5. 长时间无响应

## 参考资源

- Aider 文档：https://aider.chat/
- Aider 日志位置：https://aider.chat/docs/config/options.html
- Python Watchdog：https://python-watchdog.readthedocs.io/
- Windows 终端 API：https://docs.microsoft.com/en-us/windows/console/

## 版本历史

- v0.1.0 (MVP): Aider 日志监控支持
- v0.2.0 (Phase 2): Claude Code、Codex 终端监控
- v0.3.0 (Phase 3): 自动检测 + OCR 兜底
