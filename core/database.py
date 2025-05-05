from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import logging
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class DatabaseLifespan:
    """数据库生命周期管理器"""
    
    def __init__(self):
        self._client: AsyncIOMotorClient | None = None
        
    @property
    def client(self) -> AsyncIOMotorClient:
        if not self._client:
            raise RuntimeError("Database client not initialized")
        return self._client
        
    async def init(self):
        """初始化数据库连接"""
        if not self._client:
            self._client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                minPoolSize=settings.MONGODB_MIN_POOL_SIZE
            )
            # 测试连接
            db = self._client[settings.MONGODB_DB_NAME]
            await db.command("ping")
            logger.info("MongoDB connection established")
        else:
            logger.info("MongoDB connection already established")
            
    async def close(self):
        """关闭数据库连接"""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("MongoDB connection closed")
            
    @asynccontextmanager
    async def lifespan(self, app=None):
        """FastAPI 生命周期管理器"""
        await self.init()
        try:
            yield
        finally:
            await self.close()

# 创建全局实例
db_lifespan = DatabaseLifespan()
