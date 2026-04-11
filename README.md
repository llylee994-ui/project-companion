# AI Coding Companion - OpenClaw Skill

一个用于监控 AI 编程工具执行状态的 OpenClaw Skill，在工具完成工作时主动通知用户。

## 当前版本：MVP (v0.1.0)

**只支持 Aider 日志监控**

### 核心功能
1. **Aider 日志监控** - 监控 `~/.aider/history` 日志文件
2. **完成检测** - 检测 `"Added"`、`"Committed"`、返回提示符（`^>`）
3. **飞书通知** - 工作完成时发送飞书通知

### 技术架构（策略模式）
```
ai-coding-companion/
├── SKILL.md                    # OpenClaw Skill 配置
├── config.yaml                 # 配置文件模板
├── main.py                     # 主入口
├── src/
│   ├── strategies/            # 监控策略
│   │   ├── base.py           # 抽象基类
│   │   └── log_monitor.py    # 日志监控（Aider）
│   ├── detector.py           # 完成检测器
│   ├── notifier.py           # 通知发送
│   ├── summarizer.py         # 总结生成（未来扩展）
│   └── utils.py              # 工具函数
└── README.md                  # 本文档
```

## 快速开始

### 1. 配置
复制 `config.yaml` 模板并修改：

```yaml
version: "1.0"

projects:
  - name: "my-project"
    path: "~/projects/my-project"
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
      target: "chat:oc_xxxxxxxxxxxxxxxx"  # 你的飞书群ID

monitoring:
  check_interval: 2
  max_session_duration: 1800
```

### 2. 运行
```bash
python main.py
```

### 3. 作为 OpenClaw Skill 使用
1. 将项目目录放置在 OpenClaw 的 skills 目录中
2. 在 OpenClaw 中配置 Skill
3. 通过 OpenClaw 界面或 API 调用

## 工作原理

### 监控流程
```
1. 监控 Aider 日志文件 (~/.aider/history)
2. 实时读取新增内容
3. 检测完成标记：
   - "Added" - 文件已添加到对话
   - "Committed" - 已提交代码
   - "^>" - 返回提示符（正则表达式）
4. 检测到完成时发送飞书通知
```

### Aider 日志示例
```
> 帮我修复这个bug           # 用户输入
我来帮你修复...            # Aider 响应
修改了 src/file.py        # 文件修改
Added src/file.py         # 完成标记 → 触发通知
Committed the changes     # 另一个完成标记
>                         # 提示符 → 另一个完成标记
```

## 配置说明

### 项目配置
- `name`: 项目名称（显示在通知中）
- `path`: 项目路径（仅用于显示）
- `tool`: 工具类型（当前只支持 `"aider"`）
- `enabled`: 是否启用监控
- `aider_config.log_path`: Aider 日志文件路径
- `aider_config.completion_markers`: 完成标记列表

### 通知配置
- `enabled`: 是否启用通知
- `channels`: 通知渠道列表
  - `type`: 渠道类型（`feishu`、`discord`、`email`、`telegram`）
  - `target`: 目标地址（飞书群ID、邮箱等）

### 监控配置
- `check_interval`: 检查间隔（秒），建议 2-5 秒
- `max_session_duration`: 最大会话时长（秒），超时自动重置

## 开发说明

### 代码结构
- **策略模式设计**：便于未来扩展支持更多工具
- **模块化设计**：各功能模块独立，易于测试和维护
- **错误处理**：完善的错误处理和日志记录

### 扩展支持其他工具
未来可以通过实现新的策略类来支持其他工具：
1. `TerminalMonitor` - 终端输出监控（Claude Code、Codex）
2. `ScreenOCRMonitor` - 屏幕 OCR 监控（桌面版兜底）

### 测试
```bash
# 基本功能测试
python test_simple.py

# 端到端测试
python test_e2e.py
```

## 注意事项

1. **文件编码**：Aider 日志使用 UTF-8 编码
2. **文件锁**：日志文件可能被 Aider 占用，代码已处理此情况
3. **性能**：检查间隔不要太短（默认 2 秒）
4. **隐私**：不存储完整日志，只读取新增内容

## 未来计划

### Phase 2: 多工具支持
- Claude Code 终端监控
- Codex 进程监控
- 自动检测工具类型

### Phase 3: 完整功能
- 屏幕 OCR 监控（桌面应用兜底）
- 智能总结生成
- 权限询问提醒
- 多会话管理

## 许可证

MIT License