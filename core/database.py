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
        self._db = None
        
    @property
    def client(self) -> AsyncIOMotorClient:
        if not self._client:
            raise RuntimeError("Database client not initialized")
        return self._client
        
    @property
    def db(self):
        if not self._db:
            raise RuntimeError("Database not initialized")
        return self._db
        
    async def init(self):
        """初始化数据库连接"""
        if not self._client:
            try:
                # 使用环境感知的 MongoDB URL
                mongodb_url = settings.get_mongodb_url  # 使用 property 而不是调用方法
                logger.info(f"Connecting to MongoDB with URL: {mongodb_url}")  
                self._client = AsyncIOMotorClient(
                    mongodb_url,
                    maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                    minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
                    serverSelectionTimeoutMS=5000  
                )
                self._db = self._client[settings.MONGODB_DB_NAME]
                
                # 测试连接
                await self._client.admin.command('ping')
                logger.info(f"MongoDB connection established in {settings.ENVIRONMENT} environment")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {str(e)}")
                self._client = None  
                self._db = None
                raise
        else:
            logger.info("MongoDB connection already established")
            
    async def close(self):
        """关闭数据库连接"""
        if self._client:
            try:
                self._client.close()
                self._client = None
                self._db = None
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {str(e)}")
                raise
            
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
