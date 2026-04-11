---
name: ai-coding-companion
description: |
  AI 编程伴侣 - 监控你的 AI 工具（Claude Code、Codex、Aider 等），
  在工具完成工作时主动通知你，让你无需一直盯着屏幕等待。

  核心场景：
  - 让 Claude Code 修 bug → 去干别的 → 完成后收到通知
  - Codex 生成代码时 → 刷手机 → 完成后回来继续
  
  核心功能：
  - 终端/进程监控
  - 智能完成检测
  - 主动通知（飞书、Discord、邮件）
  - 权限询问提醒
  - 工作摘要生成

tools:
  - exec          # 执行 git 命令、文件操作
  - message       # 发送通知到各种渠道
  - read          # 读取配置文件
  - write         # 写入状态文件
  - memory_search # 可选：历史项目数据查询

cron:
  - name: check-projects
    schedule: "*/5 * * * *"      # 每5分钟检查一次
    description: 检查所有监控项目的 Git 状态
    
  - name: daily-summary
    schedule: "0 21 * * *"       # 每晚9点发送日报
    description: 发送每日项目汇总

config:
  schema: |
    type: object
    required:
      - projects
      - notification
    properties:
      projects:
        type: array
        description: 要监控的项目列表
        items:
          type: object
          required:
            - name
            - path
          properties:
            name:
              type: string
              description: 项目名称
            path:
              type: string
              description: 项目绝对路径
            branch:
              type: string
              default: "main"
              description: 监控的 Git 分支
            enabled:
              type: boolean
              default: true
              description: 是否启用监控
              
      notification:
        type: object
        required:
          - enabled
          - channels
        properties:
          enabled:
            type: boolean
            default: true
          channels:
            type: array
            items:
              type: object
              required:
                - type
                - target
              properties:
                type:
                  type: string
                  enum: [feishu, discord, email, telegram]
                target:
                  type: string
                  description: 飞书群ID/邮箱/Discord频道等
                  
      summary:
        type: object
        properties:
          mode:
            type: string
            enum: [brief, detailed, none]
            default: brief
            description: 总结详细程度
          include_ai:
            type: boolean
            default: false
            description: 是否使用 AI 生成智能总结
          max_files_to_analyze:
            type: number
            default: 50
            description: 最多分析的文件数（控制 token 消耗）
            
      permissions:
        type: object
        properties:
          mode:
            type: string
            enum: [ask, auto, silent]
            default: ask
            description: 权限请求处理方式
          auto_allow_patterns:
            type: array
            items:
              type: string
            description: 自动允许的白名单模式
            
      polling:
        type: object
        properties:
          interval:
            type: number
            default: 300
            description: 检查间隔（秒）
          max_session_gap:
            type: number
            default: 28800
            description: 最大会话间隔（秒），超过视为新会话

examples:
  - description: 初始化配置
    prompt: |
      帮我初始化 project-companion 的配置，
      监控 ~/projects/my-app，发送到飞书群 oc_xxx
    
  - description: 查看项目状态
    prompt: |
      project-companion 状态如何？
      今天完成了多少工作？
      
  - description: 手动触发总结
    prompt: |
      为 my-app 项目生成一份阶段总结

author: llylee994-ui
version: 0.1.0
license: MIT
repository: https://github.com/llylee994-ui/project-companion
