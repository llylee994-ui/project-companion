# Project Companion

智能项目伴侣 - 自动监控你的编程项目进度。

## 功能

- 🔍 自动监控 Git 仓库提交
- 📊 生成阶段总结（代码变更统计）
- 🔔 多渠道通知（飞书、Discord、邮件）
- ⏱️ 工作时长追踪
- 🤖 可选 AI 智能分析

## 安装

```bash
# 克隆仓库
git clone https://github.com/yourname/project-companion.git
cd project-companion

# 安装依赖
pip install pyyaml

# 复制配置模板
cp config.yaml.example config.yaml

# 编辑配置
nano config.yaml
```

## 配置

编辑 `config.yaml`：

```yaml
projects:
  - name: "my-project"
    path: "~/projects/my-project"
    branch: "main"
    enabled: true

notification:
  enabled: true
  channels:
    - type: "feishu"
      target: "chat:oc_xxx"

summary:
  mode: "brief"      # brief / detailed
  include_ai: false  # 是否使用 AI 生成总结
```

## 使用

### 手动运行

```bash
python main.py
```

### 作为 OpenClaw Skill

```bash
# 安装 Skill
npx skills add yourname/project-companion

# 在 OpenClaw 中使用
@openclaw 检查项目状态
```

### 自动运行（Cron）

```bash
# 每5分钟检查一次
*/5 * * * * cd /path/to/project-companion && python main.py
```

## 开发

```
project-companion/
├── SKILL.md              # OpenClaw Skill 配置
├── SPEC.md               # 详细需求文档
├── config.yaml           # 用户配置
├── main.py               # 主入口
├── src/
│   ├── __init__.py
│   ├── watcher.py        # Git 监控
│   ├── summarizer.py     # 总结生成
│   ├── notifier.py       # 通知发送
│   └── utils.py          # 工具函数
└── tests/                # 测试
```

## License

MIT
