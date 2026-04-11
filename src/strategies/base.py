"""
监控策略抽象基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class MonitorStrategy(ABC):
    """监控策略抽象基类"""
    
    @abstractmethod
    def start(self, config: Dict[str, Any]) -> bool:
        """
        启动监控
        
        Args:
            config: 策略配置
            
        Returns:
            bool: 是否成功启动
        """
        pass
    
    @abstractmethod
    def check(self) -> Dict[str, Any]:
        """
        检查状态
        
        Returns:
            dict: 状态信息 {
                "status": "working" | "completed" | "error" | "idle",
                "output": "捕获的输出内容",
                "metadata": {}  # 额外元数据
            }
        """
        pass
    
    @abstractmethod
    def stop(self):
        """停止监控"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """获取策略名称"""
        pass