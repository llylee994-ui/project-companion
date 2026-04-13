# AI Coding Companion - 一体化启动器

## 概述

一体化启动器 (`companion_launcher.py`) 是 AI Coding Companion 项目的用户友好入口。用户只需运行一个命令，即可完成：

1. **自动检测**电脑中的AI编程工具
2. **交互式选择**工具和配置
3. **自动启动**选定的AI工具
4. **全程监控**工具输出
5. **智能通知**工作完成状态

## 功能特点

### 🚀 一键启动
- 自动检测已安装的AI编程工具（Cursor, Aider, Claude Code, Codex, Tabnine等）
- 交互式配置向导，无需手动编辑配置文件
- 自动生成监控配置并启动监控进程

### 🔧 智能工具管理
- **工具检测**: 自动检测系统安装的工具
- **进程管理**: 启动、停止、状态监控
- **配置生成**: 根据选择自动生成最优配置

### 👁️ 集成监控
- 复用现有的监控系统（日志监控、终端监控）
- 自动启动监控进程
- 实时状态显示

### 📱 多种使用模式
- **交互式模式**: 逐步引导用户完成配置
- **快速启动模式**: 使用默认配置快速启动
- **命令行模式**: 支持状态查询、停止等操作

## 安装与使用

### 基本使用

```bash
# 交互式启动（推荐）
python companion_launcher.py

# 快速启动（使用第一个检测到的工具）
python companion_launcher.py quick

# 快速启动指定工具
python companion_launcher.py quick aider ~/projects/my-app

# 显示系统状态
python companion_launcher.py status

# 停止所有进程
python companion_launcher.py stop

# 显示帮助
python companion_launcher.py help
```

### 交互式启动流程

1. **工具检测**: 自动扫描系统，列出可用的AI编程工具
2. **工具选择**: 从列表中选择要使用的工具
3. **配置选择**:
   - 批准模式（自动/询问/静默/智能）
   - 项目路径
   - 通知设置
4. **自动启动**:
   - 生成监控配置
   - 启动选定的AI工具
   - 启动监控进程
5. **运行监控**: 显示运行状态，等待工作完成

## 支持的AI工具

| 工具 | ID | 描述 | 检测方式 |
|------|-----|------|----------|
| Cursor | `cursor` | AI驱动的代码编辑器 | 安装路径、命令行 |
| Aider | `aider` | 命令行AI编程助手 | Python包、命令行 |
| Claude Code | `claude_code` | Anthropic的Claude编程工具 | 应用、命令行 |
| Codex | `codex` | GitHub Copilot CLI | VS Code扩展、命令行 |
| Tabnine | `tabnine` | AI代码补全工具 | 应用、命令行 |

## 批准模式说明

### 1. 自动批准模式
- **行为**: 自动批准所有安全操作
- **适用场景**: 信任的环境，希望最小化中断
- **响应**: 自动发送回车作为"yes"

### 2. 询问模式
- **行为**: 每次权限请求都发送通知询问用户
- **适用场景**: 需要完全控制，安全敏感环境
- **响应**: 等待用户确认

### 3. 静默模式
- **行为**: 不处理权限请求
- **适用场景**: 只监控不干预
- **响应**: 忽略权限请求

### 4. 智能模式
- **行为**: 根据文件类型自动决定
- **适用场景**: 平衡安全性和便利性
- **响应**: 白名单自动批准，黑名单自动拒绝

## 文件结构

```
project-companion/
├── companion_launcher.py      # 主启动器
├── main.py                    # 原有监控主程序
├── config.yaml                # 配置文件
├── src/
│   ├── tool_detector.py       # 工具检测器
│   ├── tool_selector.py       # 交互式选择器
│   ├── tool_launcher.py       # 工具启动器
│   ├── monitor_manager.py     # 监控管理器
│   ├── strategies/            # 监控策略
│   ├── detector.py            # 完成检测器
│   └── notifier.py            # 通知发送器
└── docs/                      # 文档
```

## 技术架构

### 1. 工具检测层
- `ToolDetector`: 检测系统安装的AI工具
- 支持多平台（Windows/macOS/Linux）
- 多种检测方法（命令行、安装路径、进程）

### 2. 用户交互层
- `ToolSelector`: 交互式配置向导
- 命令行界面，支持键盘交互
- 配置验证和默认值

### 3. 工具管理层
- `ToolLauncher`: 启动和管理AI工具进程
- `ToolManager`: 管理多个工具实例
- 进程监控和错误处理

### 4. 监控集成层
- `MonitorManager`: 生成配置并启动监控
- 与现有监控系统无缝集成
- 配置保存和加载

### 5. 主控制器
- `CompanionLauncher`: 协调所有组件
- 提供多种使用模式
- 统一的错误处理和资源清理

## 扩展开发

### 添加新工具支持

1. 在 `tool_detector.py` 中添加工具定义：
```python
{
    "id": "new_tool",
    "name": "New Tool",
    "description": "工具描述",
    "detection_methods": [
        detector._detect_by_command,
        # 添加自定义检测方法
    ]
}
```

2. 在 `tool_launcher.py` 中添加启动配置：
```python
if tool_id == "new_tool":
    return {
        "command": "new_tool",
        "args": [],
        "env": {}
    }
```

3. 在 `monitor_manager.py` 中添加完成标记：
```python
if tool_id == "new_tool":
    base_markers.extend(["特定完成标记"])
```

### 自定义批准规则

修改 `monitor_manager.py` 中的 `_get_auto_response_config` 方法：

```python
def _get_auto_response_config(self, approval_mode: str) -> Dict:
    if approval_mode == "custom":
        return {
            "enabled": True,
            "allow_response": "\n",
            "deny_response": "\x03",
            "default_allow": False,
            "whitelist": ["自定义白名单"],
            "blacklist": ["自定义黑名单"]
        }
```

## 故障排除

### 常见问题

1. **工具未检测到**
   - 确保工具已正确安装
   - 检查工具是否在系统PATH中
   - 运行 `python -c "from src.tool_detector import ToolDetector; d=ToolDetector(); print(d.detect_installed_tools())"`

2. **启动失败**
   - 检查项目路径是否存在
   - 确认有足够的权限
   - 查看错误输出信息

3. **监控未启动**
   - 检查配置文件是否正确生成
   - 确认 `main.py` 可以正常运行
   - 查看监控进程输出

4. **通知未发送**
   - 检查飞书Webhook配置
   - 确认网络连接
   - 查看通知日志

### 调试模式

```bash
# 详细日志输出
set PYTHONUNBUFFERED=1
python companion_launcher.py 2>&1 | tee launch.log

# 单独测试组件
python -c "from src.tool_detector import ToolDetector; d=ToolDetector(); print(d.detect_installed_tools())"
python -c "from src.monitor_manager import MonitorManager; m=MonitorManager(); print(m.generate_config(...))"
```

## 性能优化

### 启动优化
- 工具检测缓存
- 并行检测多个工具
- 延迟加载模块

### 资源管理
- 进程资源限制
- 内存使用监控
- 自动清理僵尸进程

### 用户体验
- 进度指示器
- 配置保存和记忆
- 错误恢复机制

## 安全考虑

### 权限管理
- 最小权限原则
- 文件访问控制
- 环境变量保护

### 数据安全
- 不存储敏感信息
- 日志脱敏处理
- 安全通信通道

### 进程隔离
- 子进程沙箱
- 资源限制
- 信号处理

## 未来扩展

### 计划功能
- [ ] 图形界面版本
- [ ] 插件系统
- [ ] 远程监控支持
- [ ] 团队协作功能
- [ ] 数据分析面板

### 技术改进
- [ ] 异步IO支持
- [ ] 分布式监控
- [ ] 机器学习优化
- [ ] 自动化测试套件

## 贡献指南

1. Fork 项目仓库
2. 创建功能分支
3. 提交代码更改
4. 添加测试用例
5. 更新文档
6. 创建 Pull Request

## 许可证

MIT License

## 支持与反馈

- 问题报告: GitHub Issues
- 功能请求: GitHub Discussions
- 文档改进: Pull Requests

---

**最后更新**: 2026-04-13  
**版本**: v1.0.0 (一体化启动器)  
**状态**: ✅ 功能完整，已通过基础测试