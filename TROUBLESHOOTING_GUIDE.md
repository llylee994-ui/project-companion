# 故障排除指南

## 用户报告的问题

### 问题1：权限检测不工作
**症状**：
- 配置为 `auto` 模式时，Aider 的权限请求没有被自动处理
- 例如：`Add file to the chat? (Y)es/(N)o/(D)on't ask again [Yes]:` 没有被检测到

**原因**：
- 旧的权限检测模式没有匹配新的 Aider 提示格式
- 特别是带有 `(Y)es/(N)o/(D)on't ask again [Yes]:` 这种复杂格式的提示

**解决方案**：
已修复！更新后的权限检测器现在支持：
- `Add file to the chat?` 格式
- `Create new file? (Y)es/(N)o [Yes]:` 格式
- 各种带默认值 `[Yes]` 的格式
- 更灵活的正则表达式匹配

### 问题2：工作完成通知没有发送
**症状**：
- 权限询问时收到了飞书通知
- 但工作完成后没有收到完成通知

**可能原因**：
1. **完成标记不匹配**：Aider 的输出格式可能与配置的完成标记不匹配
2. **通知发送失败**：飞书通知可能发送失败
3. **权限检测干扰**：权限检测可能干扰了完成检测（已测试，不是这个问题）

**诊断步骤**：

#### 步骤1：检查完成标记配置
查看你的 `config.yaml` 文件中的 `completion_markers`：

```yaml
aider_config:
  completion_markers:
    - "Added"                    # 文件已添加
    - "Committed"                # 已提交代码
    - "^>"                       # 正则：返回提示符（以 > 开头的行）
```

尝试添加更多标记：
```yaml
aider_config:
  completion_markers:
    - "Added"
    - "Committed" 
    - "^>"          # 提示符 >
    - "^\\$"        # bash 提示符 $
    - "✓"           # 完成标记 ✓
    - "Done"        # 完成
    - "Finished"    # 完成
    - "Completed"   # 完成
```

#### 步骤2：检查 Aider 的实际输出
查看 Aider 日志文件，看看工作完成时实际输出什么：

```bash
# 查看 Aider 日志
tail -f ~/.aider/chat.history.md
```

注意工作完成时的最后几行输出，然后调整 `completion_markers` 以匹配。

#### 步骤3：启用调试日志
修改 `main.py` 添加更多日志输出，或运行测试脚本：

```bash
python test_complete_workflow.py
```

### 问题3：auto_approve 模式
**需求**：用户想要一个更宽松的自动批准模式

**解决方案**：
已添加 `auto_approve` 模式！配置示例：

```yaml
permissions:
  mode: "auto_approve"    # 自动批准所有权限请求
  auto_allow_patterns: []  # 白名单（在此模式下不使用）
```

模式对比：
- `ask`：总是询问用户（发送通知）
- `auto`：根据白名单自动决策
- `auto_approve`：自动批准所有请求（最宽松）
- `silent`：静默拒绝所有请求

## 配置建议

### 针对开发环境
```yaml
permissions:
  mode: "auto"
  auto_allow_patterns:
    - ".*\\.py$"           # 允许 Python 文件
    - ".*\\.txt$"          # 允许文本文件
    - ".*\\.md$"           # 允许 Markdown 文件
    - ".*test.*\\.py$"     # 允许测试文件
    - ".*docs?/.*"         # 允许文档目录

aider_config:
  completion_markers:
    - "Added"
    - "Committed"
    - "^>"
    - "^\\$"
    - "✓"
    - "Done"
```

### 针对生产环境（严格）
```yaml
permissions:
  mode: "ask"             # 总是询问
  auto_allow_patterns: [] # 无自动权限

aider_config:
  completion_markers:
    - "Added"
    - "Committed"
    - "^>"
    - "^\\$"
```

### 针对快速原型开发
```yaml
permissions:
  mode: "auto_approve"    # 自动批准所有
  auto_allow_patterns: [] # 白名单（不使用）

aider_config:
  completion_markers:
    - "Added"
    - "Committed"
    - "^>"
    - "✓"
    - "Done"
    - "Finished"
```

## 测试你的配置

### 1. 测试权限检测
```bash
python test_fixed_simple.py
```

### 2. 测试完整工作流程
```bash
python test_complete_workflow.py
```

### 3. 手动测试
1. 启动监控：
   ```bash
   python main.py
   ```

2. 在另一个终端运行 Aider 并请求修改文件

3. 观察：
   - 权限请求是否被检测到
   - 通知是否发送
   - 工作完成后通知是否发送

## 常见问题解答

### Q: 为什么权限检测到了但没有通知？
A: 检查配置的 `mode`：
- `auto` 模式：匹配白名单的文件不会发送通知（自动处理）
- `auto_approve` 模式：所有请求都不会发送通知（自动批准）
- `silent` 模式：所有请求都不会发送通知（静默拒绝）
- 只有 `ask` 模式会发送通知

### Q: 如何知道权限检测是否在工作？
A: 查看控制台输出。当权限被检测到时，你会看到类似：
```
🔐 检测到权限请求: my-project
   类型: file_edit
   决策: allow
```

### Q: 工作完成通知没有发送，但权限通知有发送？
A: 这很可能是完成标记配置问题。检查：
1. Aider 的实际输出格式
2. `completion_markers` 是否匹配
3. 尝试添加更多通用的完成标记

### Q: 如何调试通知发送问题？
A: 检查 `src/notifier.py` 中的发送逻辑，或添加日志：
```python
# 在 notifier.py 的 send 方法中添加
print(f"DEBUG: Sending to {channel_type}, target: {target}")
```

## 更新日志

### 已修复的问题
1. ✅ 权限检测模式不匹配新的 Aider 提示格式
2. ✅ 添加了 `auto_approve` 模式
3. ✅ 改进了文件路径提取
4. ✅ 增强了正则表达式匹配

### 待验证的问题
1. 🔄 工作完成通知问题（可能是配置问题）
2. 🔄 飞书通知发送稳定性

## 获取帮助

如果问题仍然存在：

1. 提供你的 `config.yaml` 配置
2. 提供 Aider 工作完成时的最后几行输出
3. 提供监控程序的日志输出
4. 描述具体的操作步骤

这样可以帮助进一步诊断问题。