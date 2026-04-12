# -*- coding: utf-8 -*-
"""
Git 监控模块
负责监听指定项目的 Git 仓库变化
"""

import os
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class GitWatcher:
    """Git 仓库监控器"""
    
    def __init__(self, project_path: str, branch: str = "main"):
        self.project_path = Path(project_path).expanduser().resolve()
        self.branch = branch
        self.state_file = self.project_path / ".project-companion" / "state.json"
        
    def is_valid_repo(self) -> bool:
        """检查是否为有效的 Git 仓库"""
        git_dir = self.project_path / ".git"
        return git_dir.exists() and git_dir.is_dir()
    
    def get_current_commit(self) -> Optional[Dict]:
        """获取当前最新提交信息"""
        if not self.is_valid_repo():
            return None
            
        try:
            # 格式: hash|subject|author|date|body
            result = subprocess.run(
                [
                    "git", "-C", str(self.project_path),
                    "log", "-1", "--format=%H|%s|%an|%ci|%b"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            parts = result.stdout.strip().split("|", 4)
            if len(parts) >= 4:
                return {
                    "hash": parts[0],
                    "subject": parts[1],
                    "author": parts[2],
                    "date": parts[3],
                    "body": parts[4] if len(parts) > 4 else ""
                }
        except subprocess.CalledProcessError:
            pass
            
        return None
    
    def get_diff_stats(self, since_commit: str) -> Dict:
        """
        获取自指定提交以来的变更统计
        
        Returns:
            {
                "files_changed": 5,
                "insertions": 320,
                "deletions": 115,
                "files": [
                    {"name": "app.py", "changes": "+50 -20"}
                ]
            }
        """
        try:
            # 获取统计摘要
            result = subprocess.run(
                [
                    "git", "-C", str(self.project_path),
                    "diff", "--stat", since_commit
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            return self._parse_diff_stats(result.stdout)
            
        except subprocess.CalledProcessError as e:
            return {"error": str(e), "files_changed": 0, "insertions": 0, "deletions": 0}
    
    def _parse_diff_stats(self, diff_output: str) -> Dict:
        """解析 git diff --stat 的输出"""
        lines = diff_output.strip().split("\n")
        
        stats = {
            "files_changed": 0,
            "insertions": 0,
            "deletions": 0,
            "files": []
        }
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("-"):
                continue
                
            # 匹配文件变更行，如：
            # src/app.py          |   50 +++++-
            # 或总计行：
            # 5 files changed, 320 insertions(+), 115 deletions(-)
            
            if "files changed" in line or "file changed" in line:
                # 总计行
                parts = line.split(",")
                for part in parts:
                    part = part.strip()
                    if "insertion" in part:
                        stats["insertions"] = int(part.split()[0])
                    elif "deletion" in part:
                        stats["deletions"] = int(part.split()[0])
            elif "|" in line:
                # 单个文件行
                file_part = line.split("|")[0].strip()
                stats["files"].append({"name": file_part})
                stats["files_changed"] += 1
        
        # 如果没有总计行，从文件数推算
        if stats["files_changed"] == 0 and stats["files"]:
            stats["files_changed"] = len(stats["files"])
            
        return stats
    
    def get_last_known_commit(self) -> Optional[str]:
        """读取上次记录的提交 hash"""
        if not self.state_file.exists():
            return None
            
        try:
            with open(self.state_file, "r") as f:
                state = json.load(f)
                return state.get("last_commit")
        except (json.JSONDecodeError, IOError):
            return None
    
    def save_last_commit(self, commit_hash: str):
        """保存当前提交 hash 到状态文件"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            "last_commit": commit_hash,
            "last_check": datetime.now().isoformat()
        }
        
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)
    
    def check_for_changes(self) -> Optional[Dict]:
        """
        检查是否有新提交
        
        Returns:
            有新提交时返回变更信息，否则返回 None
        """
        current = self.get_current_commit()
        if not current:
            return None
            
        last_known = self.get_last_known_commit()
        
        # 首次运行，只记录不通知
        if last_known is None:
            self.save_last_commit(current["hash"])
            return None
            
        # 没有新提交
        if current["hash"] == last_known:
            return None
            
        # 有新提交，获取变更统计
        diff_stats = self.get_diff_stats(last_known)
        
        # 保存新状态
        self.save_last_commit(current["hash"])
        
        return {
            "commit": current,
            "previous_commit": last_known,
            "diff": diff_stats
        }


def watch_projects(projects_config: List[Dict]) -> List[Dict]:
    """
    检查所有配置的项目
    
    Args:
        projects_config: 项目配置列表
        
    Returns:
        有变更的项目列表
    """
    changes = []
    
    for project in projects_config:
        if not project.get("enabled", True):
            continue
            
        watcher = GitWatcher(
            project["path"],
            project.get("branch", "main")
        )
        
        if not watcher.is_valid_repo():
            print(f"警告: {project['name']} 不是有效的 Git 仓库")
            continue
            
        result = watcher.check_for_changes()
        if result:
            result["project_name"] = project["name"]
            result["project_path"] = project["path"]
            changes.append(result)
    
    return changes
