import asyncio
import httpx
from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from collections import deque
from config import get_settings
from enum import Enum
from utils.ali_upload import upload_from_url

logger = logging.getLogger(__name__)

class MusicTaskStatus(str, Enum):
    """音乐生成任务状态"""
    PENDING = "PENDING"
    TEXT_SUCCESS = "TEXT_SUCCESS"
    FIRST_SUCCESS = "FIRST_SUCCESS"
    SUCCESS = "SUCCESS"
    CREATE_TASK_FAILED = "CREATE_TASK_FAILED"
    GENERATE_AUDIO_FAILED = "GENERATE_AUDIO_FAILED"
    CALLBACK_EXCEPTION = "CALLBACK_EXCEPTION"
    SENSITIVE_WORD_ERROR = "SENSITIVE_WORD_ERROR"

@dataclass
class RateLimitConfig:
    """速率限制配置"""
    max_requests: int = 20  # 最大请求数
    time_window: int = 10   # 时间窗口（秒）

@dataclass
class MusicGenerationResult:
    """音乐生成结果"""
    task_id: str
    audio_url: Optional[str] = None
    stream_audio_url: Optional[str] = None
    image_url: Optional[str] = None
    title: Optional[str] = None
    duration: Optional[int] = None
    status: MusicTaskStatus = MusicTaskStatus.PENDING
    error_message: Optional[str] = None
    oss_audio_url: Optional[str] = None  # 新增：OSS上的音频URL

class MusicGenerator:
    """音乐生成器，提供全局的音乐生成能力和速率限制管理"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        """
        初始化音乐生成器
        配置从settings获取
        """
        settings = get_settings()
        self.api_url = settings.MUSIC_API_URL
        self.token = settings.MUSIC_API_TOKEN
        self.rate_limit = RateLimitConfig(
            max_requests=settings.MUSIC_API_RATE_LIMIT_MAX_REQUESTS,
            time_window=settings.MUSIC_API_RATE_LIMIT_WINDOW
        )
        self._request_times = deque(maxlen=self.rate_limit.max_requests)
        self._client = httpx.AsyncClient(timeout=60.0)
    
    @classmethod
    async def get_instance(cls) -> "MusicGenerator":
        """获取MusicGenerator的单例实例"""
        if not cls._instance:
            async with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
        return cls._instance

    async def _check_rate_limit(self) -> None:
        """检查并等待速率限制"""
        now = datetime.now()
        
        # 清理过期的请求记录
        while self._request_times and \
              (now - self._request_times[0]) > timedelta(seconds=self.rate_limit.time_window):
            self._request_times.popleft()
        
        # 如果请求数达到限制，等待到最早的请求过期
        if len(self._request_times) >= self.rate_limit.max_requests:
            wait_time = (self._request_times[0] + 
                        timedelta(seconds=self.rate_limit.time_window) - now).total_seconds()
            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting for {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
        
        # 记录新的请求时间
        self._request_times.append(now)

    async def generate_music(
        self,
        prompt: str,
        custom_mode: bool = False,
        instrumental: bool = True,
        max_retries: int = 60,
        check_interval: float = 10.0,
        **kwargs
    ) -> MusicGenerationResult:
        """
        生成音乐
        :param prompt: 音乐提示描述
        :param custom_mode: 是否使用自定义模式
        :param instrumental: 是否为纯音乐
        :param max_retries: 最大重试次数
        :param check_interval: 检查间隔（秒）
        :param kwargs: 其他可选参数
        :return: 音乐生成结果
        """
        # 检查速率限制
        await self._check_rate_limit()
        
        # 构建请求数据
        payload = {
            "prompt": prompt,
            "customMode": custom_mode,
            "instrumental": instrumental,
            "callBackUrl": "http://localhost:8000/background_music_callback",
            "model": "V3_5"
        }
        payload.update(kwargs)
        
        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        
        try:
            # 1. 创建生成任务
            resp = await self._client.post(
                self.api_url,
                json=payload,
                headers=headers
            )
            resp.raise_for_status()
            result = resp.json()
            
            if result.get("code") != 200:
                raise httpx.HTTPError(f"API error: {result.get('msg')}")
            
            task_id = result["data"]["taskId"]
            generation_result = MusicGenerationResult(task_id=task_id)
            
            # 2. 轮询任务状态
            check_headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.token}",
            }
            
            for _ in range(max_retries):
                await asyncio.sleep(check_interval)
                
                resp = await self._client.get(
                    "https://apibox.erweima.ai/api/v1/generate/record-info",
                    params={"taskId": task_id},
                    headers=check_headers
                )
                resp.raise_for_status()
                result = resp.json()
                
                if result.get("code") != 200:
                    raise httpx.HTTPError(f"API error: {result.get('msg')}")
                
                data = result["data"]
                status = MusicTaskStatus(data["status"])
                generation_result.status = status
                generation_result.error_message = data.get("errorMessage")
                
                # 如果生成成功，获取音乐URL并上传到OSS
                if status == MusicTaskStatus.SUCCESS and data.get("response", {}).get("sunoData"):
                    suno_data = data["response"]["sunoData"][0]  # 获取第一个结果
                    audio_url = suno_data.get("audioUrl")
                    if audio_url:
                        # 上传到OSS
                        success = await upload_from_url(audio_url, "music")
                        if success:
                            # 构建OSS URL
                            filename = audio_url.split('/')[-1].split('?')[0]
                            oss_path = f"gal-test/music/{filename}"
                            settings = get_settings()
                            generation_result.oss_audio_url = f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT.replace('https://', '')}/{oss_path}"
                            generation_result.audio_url = generation_result.oss_audio_url
                        else:
                            logger.error(f"Failed to upload music to OSS: {audio_url}")
                            generation_result.audio_url = audio_url  # 如果上传失败，使用原始URL
                    
                    generation_result.stream_audio_url = suno_data.get("streamAudioUrl")
                    generation_result.image_url = suno_data.get("imageUrl")
                    generation_result.title = suno_data.get("title")
                    generation_result.duration = suno_data.get("duration")
                    break
                
                # 如果任务失败，退出轮询
                if status in [
                    MusicTaskStatus.CREATE_TASK_FAILED,
                    MusicTaskStatus.GENERATE_AUDIO_FAILED,
                    MusicTaskStatus.CALLBACK_EXCEPTION,
                    MusicTaskStatus.SENSITIVE_WORD_ERROR
                ]:
                    break
            
            return generation_result
            
        except httpx.HTTPError as e:
            logger.error(f"Music generation failed: {str(e)}")
            raise
    
    async def close(self):
        """关闭HTTP客户端"""
        await self._client.aclose()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
