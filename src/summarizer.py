"""
总结生成模块
根据 Git 变更信息生成阶段总结
"""

from datetime import datetime
from typing import Dict, Optional


class Summarizer:
    """阶段总结生成器"""
    
    def __init__(self, mode: str = "brief", include_ai: bool = False):
        """
        Args:
            mode: 总结模式 - brief（简洁）/ detailed（详细）/ none（关闭）
            include_ai: 是否使用 AI 生成智能总结
        """
        self.mode = mode
        self.include_ai = include_ai
    
    def generate(self, change_info: Dict) -> str:
        """
        生成阶段总结
        
        Args:
            change_info: watcher.check_for_changes() 返回的变更信息
            
        Returns:
            格式化的总结文本
        """
        if self.mode == "none":
            return ""
            
        if self.mode == "brief":
            return self._generate_brief(change_info)
        else:
            return self._generate_detailed(change_info)
    
    def _generate_brief(self, info: Dict) -> str:
        """生成简洁版总结"""
        commit = info["commit"]
        diff = info["diff"]
        
        lines = [
            f"🎉 项目阶段完成",
            f"",
            f"📁 项目：{info['project_name']}",
            f"📝 提交：{commit['subject']}",
            f"👤 作者：{commit['author']}",
            f"",
            f"📊 代码变更：",
            f"   文件：{diff.get('files_changed', 0)} 个",
            f"   新增：+{diff.get('insertions', 0)} 行",
            f"   删除：-{diff.get('deletions', 0)} 行",
        ]
        
        return "\n".join(lines)
    
    def _generate_detailed(self, info: Dict) -> str:
        """生成详细版总结"""
        commit = info["commit"]
        diff = info["diff"]
        
        lines = [
            f"🎉 项目阶段完成 - 详细报告",
            f"",
            f"📁 项目：{info['project_name']}",
            f"📂 路径：{info['project_path']}",
            f"",
            f"📝 提交信息：",
            f"   标题：{commit['subject']}",
            f"   作者：{commit['author']}",
            f"   时间：{self._format_time(commit['date'])}",
            f"   Hash：{commit['hash'][:8]}",
        ]
        
        if commit.get('body'):
            lines.extend([
                f"",
                f"📄 详细说明：",
                f"   {commit['body']}"
            ])
        
        lines.extend([
            f"",
            f"📊 代码统计：",
            f"   变更文件：{diff.get('files_changed', 0)} 个",
            f"   新增行数：+{diff.get('insertions', 0)}",
            f"   删除行数：-{diff.get('deletions', 0)}",
            f"   净变化：{diff.get('insertions', 0) - diff.get('deletions', 0):+d} 行",
        ])
        
        # 列出变更的文件（最多10个）
        files = diff.get('files', [])
        if files:
            lines.extend([f"", f"📋 变更文件："])
            for f in files[:10]:
                lines.append(f"   - {f['name']}")
            if len(files) > 10:
                lines.append(f"   ... 还有 {len(files) - 10} 个文件")
        
        return "\n".join(lines)
    
    def _format_time(self, time_str: str) -> str:
        """格式化时间字符串"""
        try:
            # 解析 ISO 格式时间
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return time_str
    
    def calculate_duration(self, current_time: str, previous_time: Optional[str]) -> Optional[str]:
        """
        计算工作时长
        
        Args:
            current_time: 当前提交时间（ISO 格式）
            previous_time: 上次提交时间（ISO 格式）
            
        Returns:
            格式化的时间差，如 "2小时30分钟"
        """
        if not previous_time:
            return None
            
        try:
            current = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
            previous = datetime.fromisoformat(previous_time.replace('Z', '+00:00'))
            
            duration = current - previous
            total_seconds = duration.total_seconds()
            
            # 超过8小时视为不同会话
            if total_seconds > 8 * 3600:
                return None
                
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            
            if hours > 0:
                return f"{hours}小时{minutes}分钟"
            else:
                return f"{minutes}分钟"
                
        except:
            return None


class AISummarizer(Summarizer):
    """
    AI 增强版总结生成器（进阶功能）
    调用 LLM API 生成智能分析
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude"):
        super().__init__(mode="detailed", include_ai=True)
        self.api_key = api_key
        self.model = model
    
    def generate_ai_summary(self, change_info: Dict, file_contents: Optional[list] = None) -> str:
        """
        使用 AI 生成智能总结
        
        注意：此功能会消耗 API token，请谨慎使用
        """
        # TODO: 实现 AI 调用逻辑
        # 1. 构建 prompt
        # 2. 调用 LLM API
        # 3. 解析返回结果
        
        base_summary = self._generate_detailed(change_info)
        
        ai_insights = """
💡 AI 分析（示例）：
   本次提交主要实现了用户认证模块的核心功能，
   使用了 JWT 和 bcrypt 技术栈。
   
   建议下一步：
   - 添加输入验证
   - 编写单元测试
   - 考虑刷新令牌机制
"""
        
        return base_summary + "\n" + ai_insights
