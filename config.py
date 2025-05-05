from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    
    # API Keys
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str
    DEEPSEEK_MODEL: str
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    
    # Frontend settings
    FRONTEND_URL: str
    
    # MongoDB settings
    MONGODB_URL: str = ""
    MONGODB_INTERNAL_URL: str = ""  # Railway internal MongoDB URL
    MONGODB_DB_NAME: str
    MONGODB_MAX_POOL_SIZE: int
    MONGODB_MIN_POOL_SIZE: int
    
    # Session Configuration
    SECRET_KEY: str  # 用于 cookie 会话加密
    
    # TTS API settings
    TTS_ACCESS_TOKEN: str = ""
    
    # Music API settings
    MUSIC_API_URL: str
    MUSIC_API_TOKEN: str
    MUSIC_API_RATE_LIMIT_MAX_REQUESTS: int
    MUSIC_API_RATE_LIMIT_WINDOW: int
    
    # Image Generation API
    IMAGE_API_URL: str
    IMAGE_API_APP_ID: str
    IMAGE_API_PRIVATE_KEY: str
    IMAGE_DEFAULT_TIMEOUT: float = 300.0  # 默认的超时时间（秒）
    IMAGE_DEFAULT_POLL_INTERVAL: float = 5.0  # 默认的轮询间隔（秒）
    
    # Aliyun OSS Configuration
    OSS_ACCESS_KEY_ID: str
    OSS_ACCESS_KEY_SECRET: str
    OSS_ENDPOINT: str = "https://oss-cn-shanghai.aliyuncs.com"
    OSS_BUCKET_NAME: str = "midreal-image-sh"
    
    @property
    def get_mongodb_url(self) -> str:
        """Get the appropriate MongoDB URL based on environment"""
        if self.ENVIRONMENT == "production":
            # In Railway production, use internal URL if available
            url = self.MONGODB_INTERNAL_URL or self.MONGODB_URL
            if not url:
                raise ValueError("No MongoDB URL configured for production environment")
            return url
        if not self.MONGODB_URL:
            raise ValueError("No MongoDB URL configured")
        return self.MONGODB_URL

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
