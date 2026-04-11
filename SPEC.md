# Project Companion Skill - 需求规格文档

## 项目概述

一个 OpenClaw Skill，用于监控用户的编程项目，在关键节点（如 Git 提交）自动生成阶段总结并发送通知，帮助用户追踪项目进度、理解技术决策，无需手动翻阅代码历史。

## 核心功能

### MVP 阶段（第一版）

1. **Git 提交监控**
   - 监听指定目录的 Git 仓库
   - 检测到新 commit 时触发总结
   - 支持多个项目同时监控

2. **阶段总结生成**
   - 统计代码变更（新增/修改/删除行数、文件数）
   - 提取 commit message
   - 计算本次工作时长（基于上次提交时间）

3. **通知发送**
   - 支持飞书、邮件、Discord 等渠道
   - 发送格式化的阶段报告

### 进阶功能（后续迭代）

4. **AI 智能总结**
   - 调用 LLM 分析变更内容
   - 生成技术栈总结
   - 提取下一步建议

5. **终端输出捕获**
   - 监控 Claude Code、Aider 等工具的输出
   - 捕获工具给出的建议和警告

6. **权限决策提示**
   - 检测到工具请求权限时通知用户
   - 支持白名单自动处理

## 技术架构

```
project-companion/
├── SKILL.md                    # OpenClaw 入口配置
├── config.yaml                 # 用户配置模板
├── src/
│   ├── __init__.py
│   ├── watcher.py              # Git/文件监控模块
│   ├── analyzer.py             # Git 分析模块
│   ├── summarizer.py           # 总结生成模块（本地/AI）
│   ├── notifier.py             # 通知发送模块
│   └── utils.py                # 工具函数
├── scripts/
│   └── install.ps1             # Windows 安装脚本
└── tests/
    └── test_watcher.py
```

## 配置说明

```yaml
# config.yaml
projects:
  - name: "my-web-app"
    path: "~/projects/my-web-app"
    git_branch: "main"           # 监控的分支
    
notification:
  enabled: true
  channels:
    - type: "feishu"
      target: "chat:oc_xxx"      # 飞书群ID
    - type: "email"
      target: "user@example.com"
  
summary:
  mode: "brief"                  # brief / detailed / none
  include_ai: false              # 是否调用 LLM
  
permissions:
  mode: "ask"                    # ask / auto / silent
  auto_allow_patterns:           # 白名单（auto 模式用）
    - "允许读取项目文件*"
    - "允许执行测试命令*"
  
polling:
  interval: 300                  # 检查间隔（秒）
```

## 通知消息格式

### 阶段完成通知（MVP）

```
🎉 项目阶段完成

📁 项目：my-web-app
🕐 时间：2026-04-11 15:00 ~ 17:30（2.5小时）
📝 提交：feat: 添加用户认证模块

📊 代码变更：
   新增：5 个文件，+320 行
   修改：3 个文件，+80 -70 行
   删除：1 个文件，-45 行

💡 查看详情：[链接]
```

### 阶段总结通知（进阶）

```
🎉 项目阶段完成 - 智能总结

📁 项目：my-web-app
🕐 本次工作：2.5小时

🎯 完成目标：
   - 实现了基于 JWT 的用户认证系统
   - 集成了密码哈希和验证流程

🛠️ 技术运用：
   - Python + FastAPI
   - PostgreSQL + SQLAlchemy
   - PyJWT + bcrypt

📊 代码统计：
   总计：+400 -115 行，9 个文件

💡 下一步建议：
   - 添加输入验证和错误处理
   - 编写单元测试覆盖认证流程
   - 考虑添加刷新令牌机制
```

## 关键实现要点

### 1. Git 监控

```python
# 使用 watchdog 或手动轮询
import subprocess

def get_latest_commit(repo_path):
    """获取最新提交信息"""
    result = subprocess.run(
        ['git', '-C', repo_path, 'log', '-1', '--format=%H|%s|%ci'],
        capture_output=True, text=True
    )
    return result.stdout.strip().split('|')

def get_diff_stats(repo_path, since_commit):
    """获取变更统计"""
    result = subprocess.run(
        ['git', '-C', repo_path, 'diff', '--stat', since_commit],
        capture_output=True, text=True
    )
    return parse_diff_stats(result.stdout)
```

### 2. 通知发送

```python
# 调用 OpenClaw 的 message 工具
# 或在 Skill 中配置 tools: ["message"]

def send_notification(channel, target, content):
    """发送通知"""
    # 实际通过 OpenClaw 工具调用
    pass
```

### 3. 工作时长计算

```python
from datetime import datetime

def calculate_work_duration(last_commit_time, current_commit_time):
    """计算两次提交之间的工作时长"""
    last = datetime.fromisoformat(last_commit_time)
    current = datetime.fromisoformat(current_commit_time)
    duration = current - last
    
    # 过滤掉过长的间隔（如隔夜）
    if duration.total_seconds() > 8 * 3600:  # 超过8小时
        return None  # 或返回 "跨会话"
    
    return duration
```

## OpenClaw 集成

### SKILL.md 关键配置

```yaml
name: project-companion
description: 监控项目进度，自动生成阶段总结并发送通知
tools:
  - exec          # 执行 git 命令
  - message       # 发送通知
  - read          # 读取配置文件
cron:
  - schedule: "*/5 * * * *"
    task: check_all_projects
config:
  schema: config.yaml  # 配置验证模式
```

## 开发阶段

### Phase 1: MVP（1-2天）
- [ ] 项目目录结构
- [ ] Git 监控模块
- [ ] 基础总结生成（本地统计）
- [ ] 飞书通知发送
- [ ] 配置文件支持

### Phase 2: 增强（3-5天）
- [ ] AI 总结生成
- [ ] 多项目支持
- [ ] 邮件/Discord 通知
- [ ] 工作时长智能计算

### Phase 3: 高级（1-2周）
- [ ] 终端输出捕获
- [ ] 权限决策提示
- [ ] 历史数据分析
- [ ] Web 仪表盘

## 参考资源

- OpenClaw Skill 规范：https://docs.openclaw.ai/skills
- 示例 Skill：system-watchdog（监控类）
- Python Git 库：GitPython（可选，但 subprocess 更轻量）

## 注意事项

1. **Token 节省**：默认使用本地统计，AI 总结作为可选项
2. **隐私安全**：不收集代码内容，只统计行数和文件名
3. **跨平台**：支持 Windows、macOS、Linux
4. **错误处理**：Git 命令失败时优雅降级
