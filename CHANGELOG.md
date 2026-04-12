# 更新日志

## [1.0.0] - 2024年 - 终端监控版本

### 新增功能
- **终端监控系统**：实时捕获AI工具终端输出
  - 支持Aider、Claude Code、Codex等工具
  - 使用subprocess.Popen方案（方案A）
  - 实时stdout/stderr监控
  - 进程生命周期管理

- **编码问题全面修复**：解决Windows中文乱码
  - 所有Python文件添加UTF-8编码声明
  - Windows平台自动设置sys.stdout为UTF-8编码
  - 动态编码检测和错误处理

- **文件路径提取增强**：智能提取权限相关文件
  - 支持带空格的文件路径（引号括起）
  - 支持多个文件（逗号分隔）
  - 支持中英文标签和Aider特定格式
  - 智能路径验证和清理

### 改进功能
- **权限检测器增强**：
  - 更多中文权限模式支持
  - 改进的文件提取算法
  - 更好的错误处理和恢复

- **配置系统扩展**：
  - 终端监控配置支持
  - 自动响应配置增强（allow_response/deny_response）
  - 响应延迟配置

- **测试系统完善**：
  - 终端监控单元测试
  - 编码修复验证测试
  - 文件路径提取测试

### 技术架构
- **新增模块**：
  - `src/strategies/terminal_monitor.py` - 终端监控策略
  - `src/terminal/` - 终端监控模块
    - `__init__.py`
    - `process_manager.py` - AI工具进程管理

- **代码质量**：
  - 所有主要文件添加类型提示
  - 改进的错误处理和日志记录
  - 代码重构和优化

### 配置文件更新
```yaml
# 新增终端监控配置
terminal_config:
  enabled: true
  command: "aider"
  args: ["--model", "deepseek-chat"]
  auto_response:
    enabled: true
    allow_response: "y"
    deny_response: "n"
    delay: 1
    whitelist: [".*\\.py$"]
    blacklist: [".*\\.key$"]
```

### 修复问题
1. **Windows中文乱码**：控制台显示乱码问题彻底解决
2. **文件路径提取**：复杂路径格式提取不准确
3. **权限检测**：中文权限提示检测不完整
4. **编码处理**：跨平台编码兼容性问题

### 已知问题
- 终端监控在某些交互式工具中可能需要额外处理
- 极少数特殊文件路径格式可能提取不准确
- Windows平台需要Python 3.8+版本

### 升级说明
1. 更新配置文件添加`terminal_config`部分
2. 确保所有依赖已安装
3. 测试中文显示是否正常
4. 验证终端监控功能

### 贡献者
- AI Coding Companion 开发团队

---

## [0.9.0] - 2024年 - 基础版本
### 初始功能
- 日志文件监控（Aider）
- 权限检测和通知系统
- 自动响应配置
- 基础测试框架

*注：版本号遵循语义化版本控制*