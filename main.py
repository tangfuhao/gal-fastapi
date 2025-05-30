from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import logging
from routers.auth import auth_router
from routers.games import games_router
from routers.user import user_router
from routers.admin import admin_router
from config import get_settings
from core.container import container, get_database_lifespan
import datetime
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# 初始化依赖注入容器
container.config.from_dict({
    "mongodb": {
        "url": settings.MONGODB_URL,
        "db": settings.MONGODB_DB_NAME
    }
})

# 获取数据库生命周期管理器
db_lifespan = get_database_lifespan()

app = FastAPI(
    title="Gala API", 
    description="FastAPI project", 
    version="1.0.0",
    lifespan=db_lifespan.lifespan  # 使用新的生命周期管理器
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],  # 允许的源
    allow_credentials=True,  # 允许携带凭证
    allow_methods=["*"],  # 允许的方法
    allow_headers=["*"],  # 允许的头部
)

# 配置 session
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",
    https_only=True
)

# 注册路由
app.include_router(auth_router)
app.include_router(games_router)
app.include_router(user_router)
app.include_router(admin_router)

# 健康检查端点
@app.get("/api/health")
async def health_check():
    try:
        settings = get_settings()
        # 检查数据库连接
        db_lifespan = get_database_lifespan()
        if not db_lifespan._client:  # 只有在没有连接时才初始化
            await db_lifespan.init()
        
        # 检查数据库连接
        db = container.database()
        await db.command("ping")
        
        return {
            "status": "healthy",
            "timestamp": datetime.datetime.utcnow(),
            "environment": settings.ENVIRONMENT,
            "mongodb_url": settings.get_mongodb_url.replace(settings.MONGODB_DB_NAME, "****"),  # 隐藏敏感信息
            "services": {
                "database": "connected",
                "api": "running"
            }
        }
    except ValueError as ve:
        logger.error(f"Configuration error: {str(ve)}")
        raise HTTPException(
            status_code=500,
            detail=f"Configuration error: {str(ve)}"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {str(e)}"
        )

@app.get("/")
async def root():
    """测试端点"""
    return {"message": "Hello World"}

#background_music_callback 端点 直接打印并返回
@app.post("/background_music_callback")
async def background_music_callback(request: dict):
    logger.info(f"Background music callback: {request}")
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",  # 使用字符串形式的导入路径
        host="127.0.0.1",
        port=8000,
        reload=True,  # 启用热重载
        reload_dirs=["./"],  # 监视当前目录的变化
        workers=1  # 使用单个工作进程，便于调试
    )
