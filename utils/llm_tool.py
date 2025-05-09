from typing import Dict, Any, Optional
import logging
from threading import Lock
from fastapi import HTTPException
from utils.clients import DeepSeekClient
from utils.prompt_manager import PromptManager

logger = logging.getLogger(__name__)

class LLMTool:
    """
    大模型调用工具，封装 client, prompt_manager 及大模型生成逻辑。
    """
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        prompt_replacements: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成大模型回复
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词模板名称
            temperature: 采样温度
            prompt_replacements: 提示词模板替换参数
            
        Returns:
            str: 大模型生成的回复
        """
        client = DeepSeekClient()
        prompt_manager = PromptManager()
        try:
            messages = prompt_manager.create_messages(
                system_prompt=system_prompt,
                user_prompt_name=user_prompt,
                user_params=prompt_replacements
            )
            completion = await client.chat_completion(
                messages=messages,
                temperature=temperature,
            )
            return completion
        except Exception as e:
            logger.error(f"LLMTool 执行失败: {e}")
            raise e
