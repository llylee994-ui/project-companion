# 终端输出捕获监控方案 - 技术需求文档

## 项目背景

AI Coding Companion 当前使用日志文件监控 Aider，但存在以下问题：
- Aider 终端版不总是写入日志文件
- 依赖文件 I/O，实时性较差
- 不支持同时监控多个工具实例

需要实现**终端输出直接捕获**方案，实时获取 Aider/Claude Code/Codex 的输出。

---

## 需求概述

### 核心目标
实现一个通用的终端输出捕获器，能够：
1. 启动或附加到 AI 编程工具（Aider/Claude Code/Codex）
2. 实时捕获 stdout/stderr 输出
3. 检测权限询问并触发通知
4. 支持 Windows 平台

### 支持的工具
| 工具 | 启动命令 | 特点 |
|------|---------|------|
| Aider | `aider --model <model>` | 支持多种模型，有权限确认 |
| Claude Code | `claude` | Anthropic 官方工具 |
| Codex | `codex` | OpenAI 官方工具 |
| 通用 | 自定义命令 | 支持任何终端工具 |

---

## 技术方案对比

### 方案 A：subprocess.Popen（推荐）

**原理**
使用 Python subprocess 启动工具，通过 PIPE 捕获输出流。

**优点**
- 跨平台（Windows/Linux/Mac）
- 实现简单，标准库支持
- 完全控制工具生命周期
- 可以发送输入（自动回复 y/n）

**缺点**
- 需要重新启动工具
- 无法附加到已运行的实例

**适用场景**
- 用户通过 Companion 启动工具
- 需要自动回复权限询问

**伪代码**
```python
import subprocess
import threading

class TerminalMonitor:
    def __init__(self, command, on_output=None, on_permission=None):
        self.command = command
        self.on_output = on_output
        self.on_permission = on_permission
        self.process = None
        
    def start(self):
        self.process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='ignore'
        )
        
        # 启动读取线程
        threading.Thread(target=self._read_output, daemon=True).start()
        
    def _read_output(self):
        for line in self.process.stdout:
            if self.on_output:
                self.on_output(line)
            
            # 检测权限询问
            if self._is_permission_prompt(line):
                if self.on_permission:
                    self.on_permission(line)
                    
    def send_input(self, text):
        """发送输入到工具（如 'y' 或 'n'）"""
        if self.process and self.process.stdin:
            self.process.stdin.write(text + '\n')
            self.process.stdin.flush()
            
    def _is_permission_prompt(self, line):
        """检测是否为权限询问"""
        patterns = [
            r'Apply these changes\?',
            r'Create new file\?',
            r'Run shell command\?',
            r'\(Y\)es/\(N\)o',
            # ... 更多模式
        ]
        return any(re.search(p, line) for p in patterns)
```

---

### 方案 B：Windows 终端缓冲区读取

**原理**
使用 Windows API 读取已存在终端窗口的屏幕缓冲区内容。

**优点**
- 可以附加到已运行的工具实例
- 不需要重新启动工具
- 对用户透明

**缺点**
- Windows 专用
- 实现复杂，需要处理不同终端模拟器
- 可能受终端滚动影响

**适用场景**
- 用户已经启动了工具
- 不想中断现有会话

**关键技术**
- `pywin32` 库
- `GetConsoleScreenBufferInfo`
- `ReadConsoleOutputCharacter`

---

### 方案 C：伪终端（Pseudo Terminal）

**原理**
使用操作系统提供的伪终端 API，创建虚拟终端来运行工具。

**优点**
- 最可靠，模拟真实终端
- 支持交互式程序
- 跨平台（Windows ConPTY, Unix PTY）

**缺点**
- 实现最复杂
- Windows 需要 Windows 10 1809+

**适用场景**
- 需要完整的终端模拟
- 工具需要复杂的交互

---

## 推荐实现：方案 A（subprocess）

### 核心模块设计

```
src/
├── strategies/
│   ├── base.py                    # 监控策略基类
│   ├── log_monitor.py             # 日志监控（现有）
│   └── terminal_monitor.py        # 终端监控（新增）
├── terminal/
│   ├── __init__.py
│   ├── process_manager.py         # 进程管理
│   ├── output_capture.py          # 输出捕获
│   └── input_controller.py        # 输入控制
└── detector.py                    # 权限检测器（复用现有）
```

### 类设计

```python
# src/terminal/process_manager.py

class AIProcessManager:
    """AI 工具进程管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.processes: Dict[str, subprocess.Popen] = {}
        self.callbacks: Dict[str, Callable] = {}
        
    def start_tool(self, tool_name: str, project_path: str) -> bool:
        """启动 AI 工具"""
        command = self._build_command(tool_name, project_path)
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='ignore',
            cwd=project_path
        )
        
        self.processes[tool_name] = process
        
        # 启动监控线程
        threading.Thread(
            target=self._monitor_output,
            args=(tool_name, process),
            daemon=True
        ).start()
        
        return True
        
    def _build_command(self, tool_name: str, project_path: str) -> List[str]:
        """构建启动命令"""
        commands = {
            'aider': ['aider', '--model', 'deepseek-chat'],
            'claude': ['claude'],
            'codex': ['codex'],
        }
        return commands.get(tool_name, [tool_name])
        
    def _monitor_output(self, tool_name: str, process: subprocess.Popen):
        """监控输出"""
        for line in process.stdout:
            # 调用回调
            if tool_name in self.callbacks:
                self.callbacks[tool_name](line)
                
    def send_response(self, tool_name: str, response: str):
        """发送响应（如 'y' 或 'n'）"""
        process = self.processes.get(tool_name)
        if process and process.stdin:
            process.stdin.write(response + '\n')
            process.stdin.flush()
            
    def stop_tool(self, tool_name: str):
        """停止工具"""
        process = self.processes.get(tool_name)
        if process:
            process.terminate()
            del self.processes[tool_name]
```

### 配置示例

```yaml
# config.yaml

projects:
  - name: "my-web-app"
    path: "~/projects/my-web-app"
    tool: "aider"
    enabled: true
    
    # 终端监控配置（新增）
    terminal_config:
      enabled: true                    # 启用终端监控
      auto_start: true                 # 自动启动工具
      command: "aider"                 # 启动命令
      args: ["--model", "deepseek-chat"]  # 额外参数
      env:                             # 环境变量
        DEEPSEEK_API_KEY: "${DEEPSEEK_API_KEY}"
      
      # 自动响应配置
      auto_response:
        enabled: false                 # 是否自动响应
        default: "y"                   # 默认响应（y/n/ask）
        whitelist:                     # 白名单模式
          - ".*\.txt$"
          - ".*\.md$"
        blacklist:                     # 黑名单模式
          - ".*\.key$"
          - ".*secret.*"
```

---

## 集成到现有架构

### 修改 main.py

```python
class AiderMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitors: Dict[str, Any] = {}
        
        # 新增：终端进程管理器
        from src.terminal.process_manager import AIProcessManager
        self.process_manager = AIProcessManager(config)
        
    def setup_monitors(self) -> bool:
        for project in self.projects:
            if not project.get("enabled", True):
                continue
                
            # 检查监控方式
            terminal_config = project.get("terminal_config", {})
            
            if terminal_config.get("enabled", False):
                # 使用终端监控
                self._setup_terminal_monitor(project)
            else:
                # 使用日志监控（现有）
                self._setup_log_monitor(project)
                
    def _setup_terminal_monitor(self, project: Dict[str, Any]):
        """设置终端监控"""
        project_name = project["name"]
        tool_name = project.get("tool", "aider")
        project_path = expand_path(project["path"])
        
        # 注册回调
        def on_output(line: str):
            # 检测权限询问
            permission = self.permission_detector.detect(line)
            if permission:
                self._handle_permission(project_name, permission)
                
        self.process_manager.callbacks[tool_name] = on_output
        
        # 启动工具
        if terminal_config.get("auto_start", True):
            self.process_manager.start_tool(tool_name, project_path)
```

---

## 测试计划

### 单元测试
```python
def test_terminal_monitor():
    monitor = TerminalMonitor(
        command=["echo", "Apply these changes? [y/n]"],
        on_permission=lambda line: print(f"Detected: {line}")
    )
    monitor.start()
    time.sleep(1)
    assert monitor.permission_detected
```

### 集成测试
1. 启动 Aider 终端监控
2. 让 Aider 修改文件
3. 验证权限询问被检测
4. 验证飞书通知发送
5. 测试自动回复功能

---

## 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 工具输出格式变化 | 中 | 高 | 维护多种检测模式 |
| 编码问题 | 中 | 中 | 使用 errors='ignore' |
| Windows 兼容性 | 低 | 高 | 充分测试 |
| 性能问题 | 低 | 中 | 使用线程和缓冲 |

---

## 交付物

1. `src/terminal/process_manager.py` - 进程管理器
2. `src/terminal/output_capture.py` - 输出捕获
3. `src/terminal/input_controller.py` - 输入控制
4. `src/strategies/terminal_monitor.py` - 终端监控策略
5. 测试文件和文档
6. 配置示例

---

## 优先级

1. **P0**: 基础 subprocess 捕获（方案 A）
2. **P1**: 自动响应功能
3. **P2**: 多工具支持（Aider/Claude/Codex）
4. **P3**: Windows 终端缓冲区读取（方案 B）
