# -*- coding: utf-8 -*-
"""
权限检测器
检测 Aider 的权限询问和确认提示
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class PermissionType(Enum):
    """权限类型"""
    FILE_EDIT = "file_edit"  # 文件编辑权限
    FILE_CREATE = "file_create"  # 文件创建权限
    FILE_DELETE = "file_delete"  # 文件删除权限
    GIT_COMMIT = "git_commit"  # Git 提交权限
    GIT_PUSH = "git_push"  # Git 推送权限
    UNKNOWN = "unknown"  # 未知权限类型


class PermissionDecision(Enum):
    """权限决策"""
    ALLOW = "allow"  # 允许
    DENY = "deny"  # 拒绝
    ASK = "ask"  # 询问用户
    AUTO_APPROVE = "auto_approve"  # 自动批准（更宽松的模式）


class PermissionPrompt:
    """权限提示检测结果"""
    
    def __init__(self, 
                 permission_type: PermissionType,
                 prompt_text: str,
                 matched_pattern: str,
                 files: List[str] = None,
                 metadata: Dict[str, Any] = None):
        self.permission_type = permission_type
        self.prompt_text = prompt_text
        self.matched_pattern = matched_pattern
        self.files = files or []
        self.metadata = metadata or {}
        self.timestamp = None


class PermissionDetector:
    """权限检测器"""
    
    # Aider 权限询问模式（中英文）
    PERMISSION_PATTERNS = [
        # 中文模式
        (r"是否执行这个编辑\?", PermissionType.FILE_EDIT),
        (r"是否应用这些更改\?", PermissionType.FILE_EDIT),
        (r"是否创建文件\?", PermissionType.FILE_CREATE),
        (r"是否删除文件\?", PermissionType.FILE_DELETE),
        (r"是否提交更改\?", PermissionType.GIT_COMMIT),
        (r"是否推送更改\?", PermissionType.GIT_PUSH),
        
        # 更通用的中文模式
        (r"创建文件[？?]", PermissionType.FILE_CREATE),
        (r"编辑文件[？?]", PermissionType.FILE_EDIT),
        (r"删除文件[？?]", PermissionType.FILE_DELETE),
        (r"修改文件[？?]", PermissionType.FILE_EDIT),
        (r"应用更改[？?]", PermissionType.FILE_EDIT),
        (r"执行命令[？?]", PermissionType.UNKNOWN),
        
        # 英文模式 - 文件操作
        (r"Add file to the chat\?", PermissionType.FILE_EDIT),
        (r"Create new file\?", PermissionType.FILE_CREATE),
        (r"Create this file\?", PermissionType.FILE_CREATE),
        (r"Apply these changes\?", PermissionType.FILE_EDIT),
        (r"Make these changes\?", PermissionType.FILE_EDIT),
        (r"Do you want to apply this edit\?", PermissionType.FILE_EDIT),
        (r"Delete this file\?", PermissionType.FILE_DELETE),
        (r"Edit this file\?", PermissionType.FILE_EDIT),
        (r"Modify this file\?", PermissionType.FILE_EDIT),
        
        # 英文模式 - Git 操作
        (r"Commit these changes\?", PermissionType.GIT_COMMIT),
        (r"Push these changes\?", PermissionType.GIT_PUSH),
        (r"Run git command\?", PermissionType.GIT_COMMIT),
        
        # 英文模式 - 其他
        (r"Run shell command\?", PermissionType.UNKNOWN),
        (r"Execute command\?", PermissionType.UNKNOWN),
        (r"Install package\?", PermissionType.UNKNOWN),
        
        # 通用确认模式 (匹配各种确认格式)
        (r"\([Yy]es/[Nn]o", PermissionType.UNKNOWN),  # (Yes/No 或 (yes/no
        (r"\([Yy]/[Nn]", PermissionType.UNKNOWN),  # (Y/N 或 (y/n
        (r"\[[Yy]es\]", PermissionType.UNKNOWN),  # [Yes] 默认值
        (r"\[[Yy]\]", PermissionType.UNKNOWN),  # [Y] 默认值
        
        # 非常通用的模式 (兜底)
        (r"\?.*[\[\(].*[Yy].*[\/\|\]].*[Nn].*[\]\)]", PermissionType.UNKNOWN),  # 任何包含 ? 和 Y/N 选择的
        (r"\?.*[Yy]/[Nn]", PermissionType.UNKNOWN),  # 任何 ? 后跟 Y/N 的
    ]
    
    # 文件路径提取模式 - 增强版
    FILE_PATTERNS = [
        # 带标签的单个文件路径
        r"(?:文件|file)[：:]\s*([^\s]+)",  # 文件: path 或 file: path
        r"(?:创建|create)[：:]\s*([^\s]+)",  # 创建: path 或 create: path
        r"(?:编辑|edit)[：:]\s*([^\s]+)",  # 编辑: path 或 edit: path
        r"(?:删除|delete)[：:]\s*([^\s]+)",  # 删除: path 或 delete: path
        r"(?:修改|modify)[：:]\s*([^\s]+)",  # 修改: path 或 modify: path
        r"(?:更改|change)[：:]\s*([^\s]+)",  # 更改: path 或 change: path
        
        # 带引号的路径（支持空格）
        r'["\']([^"\']+\.[a-zA-Z0-9]+)["\']',  # "file.py" 或 'file.py'
        r'["\']([^"\']+/[^"\']+)["\']',  # "path/to/file" 或 'path/to/file'
        
        # 常见的文件路径模式 - 更精确
        r'\b(?:[a-zA-Z]:[\\/](?:[^\\/:*?\"<>|\r\n]+[\\/])*[^\\/:*?\"<>|\r\n]+\.(?:py|js|ts|java|cpp|c|h|html|css|md|txt|json|yaml|yml|xml))\b',  # Windows绝对路径
        r'\b/(?:[^\\/:*?\"<>|\r\n]+/)*[^\\/:*?\"<>|\r\n]+\.(?:py|js|ts|java|cpp|c|h|html|css|md|txt|json|yaml|yml|xml)\b',  # Unix绝对路径
        r'\b(?!http://|https://|ftp://)(?:[\w\.\-]+/)*[\w\.\-]+\.(?:py|js|ts|java|cpp|c|h|html|css|md|txt|json|yaml|yml|xml)\b',  # 相对路径
        
        # 多个文件（逗号分隔）
        r'(?:文件|files)[：:]\s*([^?\n]+?)(?=\?|$)',  # 文件: file1.py, file2.py
        r'(?:编辑|edits)[：:]\s*([^?\n]+?)(?=\?|$)',  # 编辑: file1.py, file2.py
        
        # Aider 特定格式
        r'Apply changes to:\s*([^?\n]+?)(?=\?|$)',  # Apply changes to: file1.py, file2.py?
        r'Create new file:\s*([^?\n]+?)(?=\?|$)',  # Create new file: file.py?
        r'Edit file:\s*([^?\n]+?)(?=\?|$)',  # Edit file: file.py?
        r'Delete file:\s*([^?\n]+?)(?=\?|$)',  # Delete file: file.py?
    ]
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化权限检测器
        
        Args:
            config: 配置字典，包含权限相关设置
        """
        self.config = config or {}
        self.permission_config = self.config.get("permissions", {})
        self.detected_prompts: List[PermissionPrompt] = []
        
    def detect(self, content: str) -> Optional[PermissionPrompt]:
        """
        检测内容中是否包含权限询问
        
        Args:
            content: 要检测的文本内容
            
        Returns:
            PermissionPrompt 对象或 None
        """
        if not content:
            return None
            
        # 检查所有权限模式
        for pattern_str, permission_type in self.PERMISSION_PATTERNS:
            pattern = re.compile(pattern_str, re.IGNORECASE | re.DOTALL)
            match = pattern.search(content)
            
            if match:
                prompt_text = match.group(0)
                
                # 提取相关文件路径
                files = self._extract_files(content)
                
                # 创建权限提示对象
                prompt = PermissionPrompt(
                    permission_type=permission_type,
                    prompt_text=prompt_text,
                    matched_pattern=pattern_str,
                    files=files,
                    metadata={
                        "full_content": content,
                        "match_position": match.start(),
                        "permission_mode": self.permission_config.get("mode", "ask")
                    }
                )
                
                self.detected_prompts.append(prompt)
                return prompt
                
        return None
    
    def _extract_files(self, content: str) -> List[str]:
        """从内容中提取文件路径"""
        files = []
        
        # 首先尝试提取带标签的文件路径（更准确）
        labeled_patterns = [
            # 英文标签
            r'(?:file|files|create|edit|delete|modify|change)[：:]\s*([^?\n]+?)(?=\?|$)',
            r'(?:File|Files|Create|Edit|Delete|Modify|Change)[：:]\s*([^?\n]+?)(?=\?|$)',
            # 中文标签
            r'(?:文件|创建|编辑|删除|修改|更改)[：:]\s*([^?\n]+?)(?=\?|$)',
            # Aider特定格式
            r'Apply changes to:\s*([^?\n]+?)(?=\?|$)',
            r'Create new file:\s*([^?\n]+?)(?=\?|$)',
            r'Edit file:\s*([^?\n]+?)(?=\?|$)',
            r'Delete file:\s*([^?\n]+?)(?=\?|$)',
        ]
        
        for pattern_str in labeled_patterns:
            try:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                match = pattern.search(content)
                if match:
                    file_text = match.group(1).strip()
                    extracted = self._extract_files_from_text(file_text)
                    files.extend(extracted)
            except:
                continue
        
        # 如果没有找到带标签的，尝试从整个内容中提取
        if not files:
            # 查找引号内的路径
            quoted_patterns = [
                r'["\']([^"\']+\.[a-zA-Z0-9]{1,5})["\']',  # 带扩展名
                r'["\']([^"\']+/[^"\']+\.[a-zA-Z0-9]{1,5})["\']',  # 路径+扩展名
            ]
            
            for pattern_str in quoted_patterns:
                try:
                    pattern = re.compile(pattern_str)
                    matches = pattern.findall(content)
                    for match in matches:
                        if self._is_valid_file_path(match):
                            files.append(match)
                except:
                    continue
        
        # 去重
        unique_files = []
        for file_path in files:
            if file_path and file_path not in unique_files:
                unique_files.append(file_path)
        
        return unique_files
    
    def _extract_files_from_text(self, text: str) -> List[str]:
        """从文本中提取文件路径"""
        files = []
        
        # 按逗号分割
        parts = [p.strip() for p in text.split(',')]
        
        for part in parts:
            if not part:
                continue
            
            # 清理部分
            cleaned = self._clean_file_part(part)
            if cleaned and self._is_valid_file_path(cleaned):
                files.append(cleaned)
        
        return files
    
    def _clean_file_part(self, text: str) -> str:
        """清理文件部分"""
        # 移除引号
        cleaned = text.strip('\"\'')
        
        # 移除常见的提示词
        prompts_to_remove = [
            'Apply changes to', 'Create new file', 'Edit file', 
            'Delete file', 'file', 'files', 'create', 'edit',
            'delete', '文件', '创建', '编辑', '删除'
        ]
        
        for prompt in prompts_to_remove:
            if cleaned.lower().startswith(prompt.lower()):
                cleaned = cleaned[len(prompt):].lstrip(': ')
        
        return cleaned.strip()
    
    def _is_valid_file_path(self, path: str) -> bool:
        """检查是否为有效的文件路径"""
        if not path or len(path) < 2:
            return False
        
        # 检查是否包含非法字符
        illegal_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in illegal_chars:
            if char in path:
                return False
        
        # 检查文件扩展名
        valid_extensions = [
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', 
            '.html', '.css', '.md', '.txt', '.json', '.yaml', 
            '.yml', '.xml', '.csv', '.sql', '.sh', '.bat',
            '.exe', '.dll', '.so', '.dylib', '.cs', '.go',
            '.rs', '.php', '.rb', '.pl', '.lua', '.swift',
            '.kt', '.scala', '.m', '.mm', '.fs', '.vb'
        ]
        
        path_lower = path.lower()
        for ext in valid_extensions:
            if path_lower.endswith(ext):
                return True
        
        # 如果没有扩展名，检查是否看起来像路径
        if '/' in path or '\\' in path:
            # 简单的路径检查
            parts = path.replace('\\', '/').split('/')
            if len(parts) >= 2:
                last_part = parts[-1]
                if '.' in last_part:
                    # 有扩展名但不在列表中
                    return True
                # 可能是目录
                return True
        
        return False
    
    def _clean_file_path(self, file_path: str) -> str:
        """清理文件路径（兼容旧接口）"""
        return self._clean_file_part(file_path)
    
    def should_notify(self, prompt: PermissionPrompt) -> bool:
        """
        判断是否应该发送通知
        
        Args:
            prompt: 检测到的权限提示
            
        Returns:
            bool: 是否发送通知
        """
        mode = self.permission_config.get("mode", "ask")
        
        if mode in ["silent", "auto_approve"]:
            return False  # 静默模式和自动批准模式，不通知
            
        if mode == "auto":
            # 自动模式：检查白名单
            decision = self.make_decision(prompt)
            if decision in [PermissionDecision.ALLOW, PermissionDecision.AUTO_APPROVE]:
                return False  # 自动允许或自动批准，不通知
            elif decision == PermissionDecision.DENY:
                return False  # 自动拒绝，不通知
            else:
                return True  # 需要询问用户
            
        # ask 模式：总是通知
        return True
    
    def make_decision(self, prompt: PermissionPrompt) -> PermissionDecision:
        """
        根据配置自动做出权限决策
        
        Args:
            prompt: 检测到的权限提示
            
        Returns:
            PermissionDecision: 决策结果
        """
        mode = self.permission_config.get("mode", "ask")
        
        if mode == "auto_approve":
            # 自动批准模式：总是允许（最宽松）
            return PermissionDecision.AUTO_APPROVE
            
        elif mode == "auto":
            # 自动模式：检查白名单
            auto_allow_patterns = self.permission_config.get("auto_allow_patterns", [])
            
            for file_path in prompt.files:
                for pattern in auto_allow_patterns:
                    if re.match(pattern, file_path):
                        return PermissionDecision.ALLOW
            
            # 默认拒绝
            return PermissionDecision.DENY
            
        elif mode == "silent":
            # 静默模式：总是拒绝
            return PermissionDecision.DENY
            
        else:  # ask 模式
            return PermissionDecision.ASK
    
    def get_decision_message(self, prompt: PermissionPrompt, decision: PermissionDecision) -> str:
        """
        获取决策消息
        
        Args:
            prompt: 权限提示
            decision: 决策结果
            
        Returns:
            str: 格式化消息
        """
        permission_type_map = {
            PermissionType.FILE_EDIT: "文件编辑",
            PermissionType.FILE_CREATE: "文件创建",
            PermissionType.FILE_DELETE: "文件删除",
            PermissionType.GIT_COMMIT: "Git 提交",
            PermissionType.GIT_PUSH: "Git 推送",
            PermissionType.UNKNOWN: "权限请求"
        }
        
        permission_name = permission_type_map.get(prompt.permission_type, "权限请求")
        
        if prompt.files:
            files_str = ", ".join(prompt.files[:3])  # 最多显示3个文件
            if len(prompt.files) > 3:
                files_str += f" 等 {len(prompt.files)} 个文件"
            file_info = f"\n📁 涉及文件: {files_str}"
        else:
            file_info = ""
        
        if decision == PermissionDecision.AUTO_APPROVE:
            return f"✅✅ 自动批准 {permission_name}{file_info} (宽松模式)"
        elif decision == PermissionDecision.ALLOW:
            return f"✅ 自动允许 {permission_name}{file_info}"
        elif decision == PermissionDecision.DENY:
            return f"❌ 自动拒绝 {permission_name}{file_info}"
        else:  # ASK
            return f"❓ 需要确认 {permission_name}{file_info}\n📝 提示: {prompt.prompt_text[:100]}..."
    
    def clear_history(self):
        """清除检测历史"""
        self.detected_prompts = []
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """获取检测统计信息"""
        stats = {
            "total_detected": len(self.detected_prompts),
            "by_type": {},
            "by_decision": {
                "allow": 0,
                "deny": 0,
                "ask": 0,
                "auto_approve": 0
            }
        }
        
        for prompt in self.detected_prompts:
            # 按类型统计
            type_name = prompt.permission_type.value
            stats["by_type"][type_name] = stats["by_type"].get(type_name, 0) + 1
            
            # 按决策统计
            decision = self.make_decision(prompt)
            stats["by_decision"][decision.value] = stats["by_decision"].get(decision.value, 0) + 1
        
        return stats