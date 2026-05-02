# AI Coding Sentinel v3.0

Monitors Claude Code and sends Feishu / WeChat notifications — walk away while your AI works, get notified when it needs you or finishes.

## How it works

```
You start a task in Claude Code
    ↓
You walk away (摸鱼)
    ↓
Claude Code hooks → Sentinel daemon (HTTP :9599)
    ↓
├── Permission prompt detected? → Feishu / WeChat: "Claude needs your approval"
├── Task done (5 min inactivity)? → Feishu / WeChat: "Task complete — here's what changed"
├── No JSONL output for 15 min? → Feishu / WeChat: "Claude may be stuck"
```

Zero LLM tokens — summaries are generated from `git diff` and `git log`.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Edit config.yaml — set your project path and notification channel (Feishu / WeChat)

# 3. Start & open dashboard
双击 启动AI哨兵.bat        # 启动 daemon + 自动打开仪表盘

# 或命令行 (看日志)
python main.py             # 浏览器打开 http://127.0.0.1:9599
```

| 文件 | 用途 |
|------|------|
| `启动AI哨兵.bat` | 一键启动 daemon + 自动打开仪表盘 |
| `http://127.0.0.1:9599` | Web 仪表盘（状态/日志/配置编辑） |

# 4. In another terminal, install Claude Code hooks
python hooks/install.py

# Done! Now use Claude Code normally — the sentinel watches in the background
```

## Architecture

```
Claude Code (settings.json hooks)
    │  Stop / UserPromptSubmit events
    ▼
hooks/claude_hooks.py ── POST ──► Hook Server (localhost:9599)
                                       │
                          ┌────────────┼────────────┐
                          ▼            ▼            ▼
                     Session Mgr   Permission    Git Summary
                     (state mach)   Detector    (git diff/log)
                          │            │            │
                          └────────────┼────────────┘
                                       ▼
                                   Notifier
                                       │
                          ┌────────────┼────────────┐
                          ▼            ▼            ▼
                       Feishu      WeCom Bot    ServerChan
                      (飞书)      (企业微信)    (个人微信)
```

## Config (`config.yaml`)

```yaml
version: "3.0"
daemon:
  host: "127.0.0.1"
  port: 9599
  inactivity_timeout: 300   # 5 min idle after Stop = task done
  stuck_timeout: 900        # 15 min no JSONL output while WORKING = may be stuck
notification:
  enabled: true
  channels:
    - type: feishu
      webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_HOOK"
    # 或使用微信通知：
    # - type: wecom_bot
    #   webhook: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
    # - type: serverchan
    #   sendkey: "SCTxxxxxxxx"
permissions:
  notify_on_prompt: true
  cooldown_seconds: 60
projects:
  - name: "my-project"
    path: "/home/user/projects/my-project"
    enabled: true
```

## Commands

| Command | Description |
|---------|-------------|
| `python main.py` | Start daemon (foreground) |
| `python hooks/install.py` | Install Claude Code hooks |
| `python hooks/install.py --remove` | Remove hooks |
| `python hooks/install.py --dry-run` | Preview hook changes |

## Notification examples

**Permission needed:**
```
Claude Code needs your attention

Project: my-project

Prompt:
...Do you want to proceed? (y/n)

Please respond in Claude Code.
```

**Task complete:**
```
AI Coding Sentinel

Project: my-project
Duration: 3m 22s

Files: 3
Lines: +45 -12

Changed files:
  src/auth/login.py
  src/auth/middleware.py
  tests/test_auth.py

Recent commits:
  abc1234 fix: resolve JWT token expiration (@you)
```

## Commands (simpler)

| Command | Description |
|---------|-------------|
| Double-click `启动AI哨兵.bat` | Start daemon (Windows) |
| `python main.py` | Start daemon (terminal) |
| `哨兵.bat` | Add to PATH, then just type `哨兵` |
| `python hooks/install.py` | Install Claude Code hooks |
| `python hooks/install.py --remove` | Remove hooks |

## OpenClaw Integration

Two modes, no token cost for the primary path:

### Mode A: Feishu webhook (default, zero token)
The daemon sends plain-text notifications directly via Feishu webhook. This is the zero-cost path.

### Mode B: OpenClaw message tool (backup)
Enable in `config.yaml`:
```yaml
notification:
  channels:
    - type: openclaw
      enabled: true
```
When enabled, the SKILL.md cron periodically checks the daemon and forwards notifications via OpenClaw's `message` tool — useful if Feishu webhook is unavailable.

### Future: Feishu bidirectional (Phase B)
```
User sends "y" in Feishu → Feishu callback → OpenClaw → Claude Code
```
Architecture designed but not implemented — requires Feishu bot callback, OpenClaw webhook receiver, and Claude Code IPC mechanism.

## WeChat / QQ Support

| 渠道 | 状态 | 说明 |
|------|------|------|
| 企业微信机器人 (`wecom_bot`) | ✅ | 群聊添加机器人 → 复制 webhook URL |
| Server酱 (`serverchan`) | ✅ | 注册 https://sct.ftqq.com → 获取 SendKey → 推送个人微信 |
| QQ | 桩 | `src/notifier.py` 留了桩，以后加 |
