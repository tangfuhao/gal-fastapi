import os
import threading
from typing import Dict, Any, List, Optional
from pathlib import Path

class PromptManager:
    """提示词管理器（单例模式）"""
    _instance = None
    _lock = threading.Lock()
    _prompts_cache: Dict[str, str] = {}  # 添加缓存来存储已加载的提示词

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, prompt_dir: str = "prompts"):
        """
        初始化 PromptManager
        
        Args:
            prompt_dir: prompt 文件所在的目录路径
        """
        # 确保初始化代码只运行一次
        if not hasattr(self, '_initialized'):
            self.prompt_dir = Path(prompt_dir)
            if not self.prompt_dir.exists():
                self.prompt_dir.mkdir(parents=True)
            self._initialized = True
            
    def load_prompt(self, prompt_name: str) -> str:
        """
        从文件加载 prompt 模板，使用缓存优化性能
        
        Args:
            prompt_name: prompt 文件名（不需要 .txt 后缀）
            
        Returns:
            prompt 模板内容
        """
        # 先检查缓存
        if prompt_name in self._prompts_cache:
            return self._prompts_cache[prompt_name]
            
        prompt_path = self.prompt_dir / f"{prompt_name}.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
            
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            # 存入缓存
            self._prompts_cache[prompt_name] = content
            return content
            
    def format_prompt(
        self,
        prompt_name: str,
        params: Dict[str, Any],
        role: str = "user"
    ) -> Dict[str, str]:
        """
        格式化 prompt 模板
        
        Args:
            prompt_name: prompt 文件名（不需要 .txt 后缀）
            params: 用于格式化的参数字典
            role: 消息角色，默认为 "user"
            
        Returns:
            格式化后的 prompt 消息字典
        """
        template = self.load_prompt(prompt_name)
        return {
            "role": role,
            "content": template.format(**params) if params else template
        }
        
    def create_messages(
        self,
        system_prompt: str,
        user_prompt_name: str,
        user_params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        创建完整的对话消息列表
        
        Args:
            system_prompt: 系统提示词文件名
            user_prompt_name: 用户提示词文件名
            user_params: 用于格式化用户提示词的参数
            
        Returns:
            对话消息列表
        """
        messages = [
            self.format_prompt(system_prompt, {}, role="system"),
            self.format_prompt(user_prompt_name, user_params or {})
        ]
        return messages
