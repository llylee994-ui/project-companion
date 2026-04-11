"""
完成检测器
检测 AI 工具的工作完成状态
"""

import re
import time
from datetime import datetime
from typing import Dict, Any, List, Optional


class CompletionDetector:
    """完成检测器"""
    
    def __init__(self, markers: List[str]):
        """
        Args:
            markers: 完成标记列表，支持普通字符串和正则表达式
                    正则表达式以 "^" 开头，如 "^>" 表示匹配以 > 开头的行
        """
        self.markers = markers
        self.start_time: Optional[datetime] = None
        self.buffer: List[str] = []
        self.session_active = False
        
    def start_session(self):
        """开始新会话"""
        self.start_time = datetime.now()
        self.buffer = []
        self.session_active = True
        print(f"开始新工作会话: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def end_session(self):
        """结束当前会话"""
        self.session_active = False
        print(f"工作会话结束")
    
    def feed(self, content: str) -> Dict[str, Any]:
        """
        输入新内容，检测是否完成
        
        Args:
            content: 新捕获的内容
            
        Returns:
            dict: 检测结果 {
                "completed": bool,
                "duration": str or None,
                "summary": str,
                "full_output": str,
                "matched_marker": str or None
            }
        """
        if not self.session_active:
            # 如果会话未激活，自动开始新会话
            self.start_session()
        
        # 添加到缓冲区
        if content:
            self.buffer.append(content)
        
        # 检查所有标记
        combined = "".join(self.buffer[-20:])  # 最近20条内容
        
        for marker in self.markers:
            matched = False
            matched_marker = None
            
            if marker.startswith("^"):
                # 正则表达式匹配
                pattern = marker[1:]  # 去掉 ^
                try:
                    if re.search(pattern, combined, re.MULTILINE):
                        matched = True
                        matched_marker = marker
                except re.error:
                    print(f"警告: 无效的正则表达式: {marker}")
            else:
                # 普通字符串匹配
                if marker in combined:
                    matched = True
                    matched_marker = marker
            
            if matched:
                return self._build_result(matched_marker)
        
        # 未检测到完成
        return {
            "completed": False,
            "duration": None,
            "summary": "",
            "full_output": "",
            "matched_marker": None
        }
    
    def _build_result(self, matched_marker: str) -> Dict[str, Any]:
        """构建完成结果"""
        if not self.start_time:
            duration_str = "未知"
        else:
            duration = datetime.now() - self.start_time
            duration_str = self._format_duration(duration)
        
        return {
            "completed": True,
            "duration": duration_str,
            "summary": self._generate_summary(),
            "full_output": "".join(self.buffer),
            "matched_marker": matched_marker
        }
    
    def _format_duration(self, delta) -> str:
        """格式化时长"""
        total_seconds = int(delta.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}秒"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            if seconds == 0:
                return f"{minutes}分钟"
            return f"{minutes}分{seconds}秒"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if minutes == 0:
                return f"{hours}小时"
            return f"{hours}小时{minutes}分钟"
    
    def _generate_summary(self) -> str:
        """生成工作摘要"""
        full_text = "".join(self.buffer)
        lines = []
        
        # 统计关键信息
        if "Added" in full_text:
            count = full_text.count("Added")
            lines.append(f"添加了 {count} 个文件到对话")
        
        if "Committed" in full_text:
            lines.append("提交了代码变更")
        
        # 检测文件修改
        if "修改了" in full_text or "modified" in full_text.lower():
            # 简单统计修改的文件数
            modified_patterns = ["修改了", "modified", "changed"]
            for pattern in modified_patterns:
                if pattern in full_text.lower():
                    # 尝试提取文件数
                    import re
                    match = re.search(r'(\d+)\s*个?文件', full_text)
                    if match:
                        lines.append(f"修改了 {match.group(1)} 个文件")
                    else:
                        lines.append("修改了文件")
                    break
        
        # 检测修复的问题
        if "修复" in full_text or "fix" in full_text.lower():
            lines.append("修复了问题")
        
        if "添加" in full_text and "Added" not in full_text:
            lines.append("添加了新功能")
        
        return "\n".join(lines) if lines else "完成工作"
    
    def is_session_active(self) -> bool:
        """检查会话是否活跃"""
        return self.session_active
    
    def get_session_duration(self) -> Optional[str]:
        """获取当前会话时长"""
        if not self.start_time or not self.session_active:
            return None
        duration = datetime.now() - self.start_time
        return self._format_duration(duration)
    
    def reset(self):
        """重置检测器状态"""
        self.start_time = None
        self.buffer = []
        self.session_active = False