# AI Coding Companion - 使用指南

## 问题解决：Aider启动黑屏问题

### 问题描述
运行 `python companion_launcher.py` 选择Aider时，弹出一块没有内容的黑屏。

### 问题原因
Aider默认使用 `--model deepseek-chat` 参数启动，但用户可能：
1. 没有安装 `deepseek-chat` 模型
2. 想使用其他模型（如 `deepseek/deepseek-chat`、`gpt-4`、`claude-3`等）
3. 需要配置API密钥或其他参数

### 解决方案
我已经修改了代码，现在启动器会询问用户使用哪个模型。

## 新功能：交互式模型配置

### 使用步骤

1. **运行启动器**
   ```bash
   python companion_launcher.py
   ```

2. **选择Aider工具**
   ```
   ✅ 检测到 X 个工具:
   ----------------------------------------
   1. ✅ Aider - 命令行AI编程助手
   ...
   ```

3. **配置Aider模型**
   ```
   🤖 Aider模型配置:
   提示: Aider需要指定使用的AI模型
   常用模型选项:
   1. deepseek-chat (默认，免费)
   2. deepseek/deepseek-chat (官方)
   3. gpt-4 (OpenAI)
   4. claude-3 (Anthropic)
   5. 自定义模型
   
   选择模型 (1-5, 默认1):
   ```

4. **选择模型**
   - 输入 `1` 使用 `deepseek-chat`（默认）
   - 输入 `2` 使用 `deepseek/deepseek-chat`（官方版本）
   - 输入 `3` 使用 `gpt-4`
   - 输入 `4` 使用 `claude-3`
   - 输入 `5` 自定义模型名称

5. **添加额外参数（可选）**
   ```
   是否添加其他Aider参数? (y/n, 默认n): y
   提示: 可以添加如 --api-key, --temperature 等参数
   格式: --参数名 值 (多个参数用空格分隔)
   请输入额外参数: --api-key sk-xxx --temperature 0.7
   ```

## 快速启动命令

### 1. 使用默认模型
```bash
python companion_launcher.py quick aider .
```
这会使用 `deepseek-chat` 模型启动Aider。

### 2. 使用特定模型
```bash
# 使用 deepseek/deepseek-chat
python companion_launcher.py quick aider . --model deepseek/deepseek-chat

# 使用 gpt-4
python companion_launcher.py quick aider . --model gpt-4

# 使用 claude-3
python companion_launcher.py quick aider . --model claude-3
```

### 3. 带额外参数
```bash
# 带API密钥和温度参数
python companion_launcher.py quick aider . --model gpt-4 --api-key sk-xxx --temperature 0.7
```

## 支持的模型列表

| 模型名称 | 类型 | 是否需要API密钥 | 备注 |
|---------|------|----------------|------|
| `deepseek-chat` | 免费 | 否 | 默认选项，国内可用 |
| `deepseek/deepseek-chat` | 官方 | 是 | 需要DeepSeek API密钥 |
| `gpt-4` | OpenAI | 是 | 需要OpenAI API密钥 |
| `gpt-3.5-turbo` | OpenAI | 是 | 性价比高 |
| `claude-3` | Anthropic | 是 | 需要Claude API密钥 |
| `claude-2` | Anthropic | 是 | 旧版本 |
| `gemini-pro` | Google | 是 | 需要Google API密钥 |

## 常见问题解决

### Q1: 如何获取API密钥？
- **DeepSeek**: 访问 https://platform.deepseek.com/
- **OpenAI**: 访问 https://platform.openai.com/
- **Anthropic**: 访问 https://console.anthropic.com/
- **Google**: 访问 https://makersuite.google.com/

### Q2: 如何设置环境变量？
可以在启动前设置环境变量：
```bash
# Windows
set DEEPSEEK_API_KEY=your_key_here
python companion_launcher.py

# macOS/Linux
export DEEPSEEK_API_KEY=your_key_here
python companion_launcher.py
```

### Q3: 如何保存配置？
启动器会自动保存配置到 `config.yaml` 文件，下次启动时会读取。

### Q4: 如何修改已保存的配置？
1. 直接编辑 `config.yaml` 文件
2. 或重新运行 `python companion_launcher.py` 生成新配置

## 高级配置

### 配置文件示例
```yaml
# config.yaml
projects:
  - name: "Aider监控"
    path: "."
    tool: "aider"
    enabled: true
    terminal_config:
      enabled: true
      auto_start: true
      command: "aider"
      args:
        - "--model"
        - "deepseek/deepseek-chat"
        - "--api-key"
        - "${DEEPSEEK_API_KEY}"
      completion_markers:
        - "Added"
        - "Committed"
        - "^>"
```

### 环境变量支持
可以在 `args` 中使用环境变量：
```yaml
args:
  - "--model"
  - "gpt-4"
  - "--api-key"
  - "${OPENAI_API_KEY}"  # 从环境变量读取
```

## 故障排除

### 1. Aider启动失败
**症状**: 黑屏或立即退出
**解决**:
- 检查模型名称是否正确
- 确认API密钥有效
- 尝试使用 `aider --help` 测试命令行

### 2. 权限检测不工作
**症状**: 权限询问时没有自动响应
**解决**:
- 检查 `permissions.mode` 配置
- 确认 `auto_response.enabled` 为 `true`

### 3. 通知不发送
**症状**: 工作完成时没有收到通知
**解决**:
- 检查飞书Webhook配置
- 确认 `notification.enabled` 为 `true`

## 更新日志

### v1.1.0 (2026-04-13)
- ✅ 添加交互式模型配置
- ✅ 支持多种AI模型
- ✅ 支持额外参数配置
- ✅ 改进用户界面

### v1.0.0 (2026-04-13)
- ✅ 基础一体化启动器
- ✅ 工具自动检测
- ✅ 权限检测和响应
- ✅ 完成监控和通知

## 获取帮助

1. 查看帮助信息
   ```bash
   python companion_launcher.py help
   ```

2. 查看状态
   ```bash
   python companion_launcher.py status
   ```

3. 停止所有进程
   ```bash
   python companion_launcher.py stop
   ```

4. 运行测试
   ```bash
   python test_aider_model.py
   python test_simple.py
   ```