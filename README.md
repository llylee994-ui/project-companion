# AI Coding Companion - 一体化启动器

一个智能的AI编程伴侣，自动检测、启动和监控AI编程工具，在工作完成时主动通知用户。

## 🚀 当前版本：v2.0 (一体化启动器版)

**支持多工具检测 + 交互式配置 + 一体化启动**

### ✨ 核心功能
1. **一体化启动** - 一个命令完成所有操作
2. **工具自动检测** - 扫描系统安装的AI编程工具
3. **交互式配置** - 引导用户完成工具和模型选择
4. **智能监控** - 实时监控工具输出和权限请求
5. **自动通知** - 工作完成时发送多通道通知
6. **权限管理** - 智能检测和自动响应权限询问

### 🏗️ 技术架构
```
project-companion/
├── companion_launcher.py      # 一体化启动器（主入口）
├── main.py                    # 主监控程序
├── config.yaml                # 配置文件模板
├── src/                       # 源代码目录
│   ├── tool_detector.py       # 工具检测器
│   ├── tool_selector.py       # 交互式选择器
│   ├── tool_launcher.py       # 工具启动器
│   ├── monitor_manager.py     # 监控管理器
│   ├── detector.py            # 完成检测器
│   ├── permission_detector.py # 权限检测器
│   ├── notifier.py            # 通知系统
│   ├── summarizer.py          # 总结生成器
│   ├── aider_detector.py      # Aider日志检测
│   ├── utils.py               # 工具函数
│   ├── watcher.py             # Git监控
│   └── __init__.py
├── docs/                      # 文档目录
├── SPEC.md                    # 需求规格文档
├── SKILL.md                   # OpenClaw Skill配置
├── PROGRESS_AND_ROADMAP.md    # 进度和路线图
├── LAUNCHER_README.md         # 启动器详细文档
├── USAGE_GUIDE.md             # 使用指南
├── PROJECT_STATUS.md          # 项目状态总结
└── README.md                  # 本文档
```

## 🚀 快速开始

### 方式一：交互式启动（推荐）
```bash
# 运行一体化启动器
python companion_launcher.py

# 按照提示：
# 1. 选择AI编程工具（如Aider）
# 2. 选择AI模型（如deepseek-chat、gpt-4等）
# 3. 选择批准模式
# 4. 设置项目路径
# 5. 系统自动启动工具和监控
```

### 方式二：快速启动
```bash
# 快速启动Aider（使用默认配置）
python companion_launcher.py quick aider .

# 快速启动指定模型
python companion_launcher.py quick aider . --model deepseek/deepseek-chat

# 快速启动带额外参数
python companion_launcher.py quick aider . --model gpt-4 --api-key sk-xxx
```

### 方式三：传统监控模式
```bash
# 编辑config.yaml配置文件
# 然后运行主监控程序
python main.py
```

### 方式四：Windows 桌面快捷方式（无需命令行）
```bash
# 双击运行
启动AI伴侣.bat
```

### 其他命令
```bash
# 查看运行状态
python companion_launcher.py status

# 停止所有进程
python companion_launcher.py stop

# 显示帮助信息
python companion_launcher.py help
```

---

## 🪟 Windows 用户特别说明

### 解决输出缓冲问题
Windows 上 Python 输出可能被缓冲，导致看不到实时输出。使用 `-u` 参数：
```bash
python -u companion_launcher.py
python -u main.py
```

或者设置环境变量：
```bash
set PYTHONUNBUFFERED=1
python companion_launcher.py
```

### 解决中文编码问题
如果遇到中文乱码，先设置 UTF-8 编码：
```bash
chcp 65001
python companion_launcher.py
```

## 🛠️ 工作原理

### 一体化启动流程
```
1. 工具检测 → 扫描系统安装的AI编程工具
2. 交互式配置 → 引导用户选择工具、模型、批准模式
3. 自动启动 → 启动选定的AI工具进程
4. 实时监控 → 捕获工具输出，检测权限询问和工作完成
5. 智能响应 → 自动响应权限请求，发送完成通知
6. 资源管理 → 统一管理所有进程，优雅退出
```

### 支持的AI工具
- **Aider** - 命令行AI编程助手
- **Claude Code** - Anthropic的Claude编程工具
- **Cursor** - AI驱动的代码编辑器
- **Codex** - GitHub Copilot CLI
- **Tabnine** - AI代码补全工具

### 智能功能
1. **权限检测** - 自动检测各种权限询问格式
2. **自动响应** - 根据配置自动响应权限请求
3. **完成检测** - 智能检测工作完成状态
4. **摘要生成** - 自动生成工作摘要
5. **多通道通知** - 支持飞书、Discord、邮件等

### Aider 日志示例
```
> 帮我修复这个bug           # 用户输入
我来帮你修复...            # Aider 响应
修改了 src/file.py        # 文件修改
Added src/file.py         # 完成标记 → 触发通知
Committed the changes     # 另一个完成标记
>                         # 提示符 → 另一个完成标记
```

## ⚙️ 配置说明

### 配置文件 (`config.yaml`)
```yaml
version: "2.0"

# 项目配置（一体化启动器会自动生成）
projects:
  - name: "Aider监控"
    path: "."
    tool: "aider"
    enabled: true
    terminal_config:
      enabled: true
      auto_start: true
      command: "aider"
      args: ["--model", "deepseek-chat"]  # 用户选择的模型
      completion_markers: ["Added", "Committed", "^>", "✓"]
      auto_response:
        enabled: true
        allow_response: "\n"  # 回车作为yes
        deny_response: "\x03" # Ctrl+C作为no

# 通知配置
notification:
  enabled: true
  channels:
    - type: "feishu"
      target: "chat:oc_xxx"
      webhook: "https://open.feishu.cn/..."

# 监控配置
monitoring:
  check_interval: 2
  max_session_duration: 1800

# 权限配置
permissions:
  mode: "auto"  # ask/auto/auto_approve/silent
  auto_allow_patterns:
    - ".*\\.py$"
    - ".*\\.txt$"
    - ".*\\.md$"
```

### 主要配置项
- **projects**: 监控的项目列表（一体化启动器自动管理）
- **notification**: 通知渠道配置
- **monitoring**: 监控参数设置
- **permissions**: 权限处理配置

### 环境变量支持
可以在配置中使用环境变量：
```yaml
args: ["--model", "gpt-4", "--api-key", "${OPENAI_API_KEY}"]
```

---

## 📚 详细文档

### 核心文档
- `LAUNCHER_README.md` - 启动器详细使用指南
- `USAGE_GUIDE.md` - 完整使用教程和问题解决
- `PROJECT_STATUS.md` - 项目状态总结
- `CLEANUP_GUIDE.md` - 项目清理指南

### 技术文档
- `SPEC.md` - 需求规格文档
- `PROGRESS_AND_ROADMAP.md` - 开发进度和路线图
- `SKILL.md` - OpenClaw Skill配置

## 🛠️ 开发说明

### 代码架构
- **模块化设计** - 各组件职责清晰，易于维护
- **类型安全** - 完整的类型注解
- **错误处理** - 完善的异常处理机制
- **资源管理** - 自动清理进程和资源
- **跨平台** - 支持Windows/macOS/Linux

### 扩展开发
项目采用模块化设计，易于扩展：
1. 添加新工具：在 `tool_detector.py` 中添加检测逻辑
2. 添加新功能：创建新的模块并集成到启动器
3. 修改配置：更新配置生成逻辑

## ⚠️ 注意事项

1. **模型适配**：选择适合自己环境的AI模型
2. **API密钥**：使用付费模型时需要配置API密钥
3. **网络连接**：通知功能需要网络连接
4. **权限设置**：根据安全需求配置权限模式
5. **资源占用**：长时间运行监控会占用系统资源

## 🔮 未来计划

### 短期计划
- 实际部署测试和验证
- 完善监控策略模块
- 性能优化和错误处理增强

### 长期计划
- 图形界面版本开发
- AI智能总结生成
- 团队协作功能
- 云端监控服务

## 📞 支持与反馈

### 获取帮助
```bash
# 查看帮助信息
python companion_launcher.py help

# 查看运行状态
python companion_launcher.py status
```

### 问题报告
1. 检查 `USAGE_GUIDE.md` 中的常见问题
2. 查看 `TROUBLESHOOTING_GUIDE.md` 故障排除
3. 检查配置文件和日志输出

---

**项目状态**: ✅ 功能完整，代码就绪  
**最后更新**: 2026年4月13日  
**版本**: v2.0 (一体化启动器版)  
**许可证**: MIT License