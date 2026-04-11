# 开发指南

## 给 Aider 的提示

### 项目背景
这是一个 OpenClaw Skill，用于监控 Git 项目并生成阶段总结。

### OpenClaw Skill 是什么？
- OpenClaw 是一个 AI 助手框架
- Skill 是扩展 OpenClaw 功能的插件
- SKILL.md 是 Skill 的入口配置（类似 package.json）
- Skill 可以通过 tools 声明使用 OpenClaw 的能力（如发送消息、执行命令）

### 当前进度
- ✅ 需求文档（SPEC.md）
- ✅ 基础目录结构
- ✅ SKILL.md 配置
- ✅ 核心模块框架（watcher, summarizer, notifier, utils）
- ⬜ 需要完善具体实现
- ⬜ 需要添加测试
- ⬜ 需要处理错误边界

### 下一步任务

1. **完善 watcher.py**
   - 测试 Git 命令是否能正确执行
   - 处理各种边缘情况（空仓库、无提交等）
   - 添加日志记录

2. **完善 notifier.py**
   - 实现真正的 OpenClaw 工具调用
   - 或者提供命令行版的发送功能

3. **添加测试**
   - 为每个模块编写单元测试
   - 模拟 Git 仓库进行测试

4. **错误处理**
   - 添加 try-except 块
   - 提供友好的错误信息

### 技术栈
- Python 3.8+
- 依赖：pyyaml
- Git 命令行工具

### 参考
- OpenClaw 文档：https://docs.openclaw.ai
- SKILL.md 中的配置规范
