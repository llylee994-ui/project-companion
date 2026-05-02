---
name: ai-coding-sentinel
description: |
  AI Coding Sentinel — monitors Claude Code (via hooks) and sends Feishu
  notifications when tasks complete or permission prompts appear, so you
  can walk away during long AI tasks.

  How it works:
  1. Start the sentinel daemon: `python main.py`
  2. Install Claude Code hooks: `python hooks/install.py`
  3. Claude Code hooks forward Stop/UserPromptSubmit events to the daemon
  4. Daemon detects permission prompts and task completion
  5. Sends Feishu notifications — you come back when needed

tools:
  - exec
  - message
  - read
  - write

config:
  schema: |
    type: object
    required:
      - projects
      - notification
    properties:
      daemon:
        type: object
        properties:
          host:
            type: string
            default: "127.0.0.1"
          port:
            type: number
            default: 9599
          inactivity_timeout:
            type: number
            default: 300
            description: Seconds of inactivity before considering task done
      notification:
        type: object
        properties:
          enabled:
            type: boolean
            default: true
          channels:
            type: array
            items:
              type: object
              properties:
                type:
                  type: string
                  enum: [feishu, wechat, qq]
                webhook:
                  type: string
                  description: Webhook URL (feishu)
      permissions:
        type: object
        properties:
          notify_on_prompt:
            type: boolean
            default: true
          cooldown_seconds:
            type: number
            default: 60
      projects:
        type: array
        items:
          type: object
          properties:
            name:
              type: string
            path:
              type: string
            enabled:
              type: boolean
              default: true

examples:
  - description: Start the daemon
    prompt: Run `python main.py` to start the sentinel daemon

  - description: Install hooks into Claude Code
    prompt: Run `python hooks/install.py` to install Stop/UserPromptSubmit hooks

  - description: Check daemon status
    prompt: |
      Check if the sentinel daemon is running on port 9599

author: llylee994-ui
version: 3.0.0
license: MIT
repository: https://github.com/llylee994-ui/project-companion
