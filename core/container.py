from dependency_injector import containers, providers
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from models.db_runtime_game import DBRuntimeGame
from models.user import DBUser
from repositories.base_repository import BaseRepository
from repositories.mongo_repository import MongoRepository
from models.game import DBGame
from models.credits import DBCredits
from models.credits_history import DBCreditsHistory
from config import get_settings
from core.database import db_lifespan
from repositories.credits_repository import CreditsRepository
from functools import lru_cache

settings = get_settings()

class Container(containers.DeclarativeContainer):
    """依赖注入容器"""
    
    # 配置
    config = providers.Configuration()
    
    # 数据库生命周期管理器
    database_lifespan = providers.Singleton(lambda: db_lifespan)
    
    # MongoDB 客户端 (从生命周期管理器获取)
    client = providers.Singleton(
        lambda lifespan: lifespan.client,
        lifespan=database_lifespan
    )
    
    # 数据库
    database = providers.Singleton(
        lambda client: client[settings.MONGODB_DB_NAME],
        client=client
    )
    
    # Collections
    games_collection = providers.Singleton(
        lambda db: db.get_collection("games"),
        db=database
    )
    
    runtime_games_collection = providers.Singleton(
        lambda db: db.get_collection("runtime_games"),
        db=database
    )
    
    users_collection = providers.Singleton(
        lambda db: db.get_collection("users"),
        db=database
    )

    credits_collection = providers.Singleton(
        lambda db: db.get_collection("credits"),
        db=database
    )

    credits_history_collection = providers.Singleton(
        lambda db: db.get_collection("credits_history"),
        db=database
    )
    
    # Repositories
    game_repository = providers.Singleton(
        MongoRepository[DBGame],
        collection=games_collection,
        model_class=DBGame
    )

    runtime_game_repository = providers.Singleton(
        MongoRepository[DBRuntimeGame],
        collection=runtime_games_collection,
        model_class=DBRuntimeGame
    )

    user_repository = providers.Singleton(
        MongoRepository[DBUser],
        collection=users_collection,
        model_class=DBUser
    )

    credits_repository = providers.Singleton(
        CreditsRepository,
        collection=credits_collection,
        history_collection=credits_history_collection
    )

    credits_history_repository = providers.Singleton(
        MongoRepository[DBCreditsHistory],
        collection=credits_history_collection,
        model_class=DBCreditsHistory
    )

# 创建全局容器实例
container = Container()

# 获取容器实例
def get_container() -> Container:
    return container

# 获取仓库的依赖函数
def get_game_repository() -> BaseRepository[DBGame]:
    return container.game_repository()

def get_runtime_game_repository() -> BaseRepository[DBRuntimeGame]:
    return container.runtime_game_repository()

def get_user_repository() -> BaseRepository[DBUser]:
    return container.user_repository()

def get_credits_repository() -> CreditsRepository:
    return container.credits_repository()

def get_credits_history_repository() -> BaseRepository[DBCreditsHistory]:
    return container.credits_history_repository()


# 获取数据库生命周期管理器
def get_database_lifespan():
    return container.database_lifespan()
