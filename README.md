# AI Coding Companion v3.0

Monitors Claude Code and sends Feishu notifications — walk away while your AI works, get notified when it needs you or finishes.

## How it works

```
You start a task in Claude Code
    ↓
You walk away (摸鱼)
    ↓
Claude Code hooks → Companion daemon (HTTP :9599)
    ↓
├── Permission prompt detected? → Feishu: "Claude needs your approval"
├── Task done (5 min inactivity)? → Feishu: "Task complete — here's what changed"
```

Zero LLM tokens — summaries are generated from `git diff` and `git log`.

## Quick Start

```bash
# 1. Install dependencies
pip install pyyaml

# 2. Edit config.yaml — set your project path and Feishu webhook

# 3. Start the daemon
python main.py

# 4. In another terminal, install Claude Code hooks
python hooks/install.py

# Done! Now use Claude Code normally — the companion watches in the background
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
                                  Feishu Webhook
```

## Config (`config.yaml`)

```yaml
version: "3.0"
daemon:
  host: "127.0.0.1"
  port: 9599
  inactivity_timeout: 300   # 5 min idle = task done
notification:
  enabled: true
  channels:
    - type: feishu
      webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_HOOK"
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
AI Coding Companion

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
| Double-click `启动AI伴侣.bat` | Start daemon (Windows) |
| `python main.py` | Start daemon (terminal) |
| `companion.bat` | Add to PATH, then just type `companion` |
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

## Future: WeChat / QQ

Notifier stubs for WeChat and QQ are in `src/notifier.py`. Add channel config when ready.
