import logging
import httpx
from typing import Dict, Optional
from openai import AsyncOpenAI
from config import get_settings
import threading


logger = logging.getLogger(__name__)

class DeepSeekClient:
    """DeepSeek API 客户端（单例模式）"""
    _instance = None
    _lock = threading.Lock()
    _client = None

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 由于是单例，需要确保初始化代码只运行一次
        if not hasattr(self, '_initialized'):
            settings = get_settings()
            self.base_url = settings.DEEPSEEK_BASE_URL
            self.model = settings.DEEPSEEK_MODEL
            if hasattr(settings, 'DEEPSEEK_API_KEY'):
                self.api_key = settings.DEEPSEEK_API_KEY
            else:
                raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
            self._initialized = True

    def _get_client(self) -> AsyncOpenAI:
        """懒加载获取异步 OpenAI 客户端，确保连接池复用"""
        if self._client is None:
            with self._lock:
                if self._client is None:
                    self._client = AsyncOpenAI(
                        api_key=self.api_key,
                        base_url=self.base_url,
                        http_client=httpx.AsyncClient(timeout=60.0)
                    )
        return self._client

    async def chat_completion(
        self,
        messages: list[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        发送聊天请求到 DeepSeek API
        
        Args:
            messages: 对话消息列表
            model: 可选，指定模型名称
            temperature: 采样温度，控制输出的随机性
        
        Returns:
            API 响应的文本内容
        
        Raises:
            Exception: API 调用失败时抛出异常
        """
        logger.info("Sending request to DeepSeek API")
        
        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                stream=False
            )
            logger.info("Successfully received response from DeepSeek API")
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Error occurred: %s", str(e))
            raise
