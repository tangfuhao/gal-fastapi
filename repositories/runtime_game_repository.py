from motor.motor_asyncio import AsyncIOMotorCollection
from models.db_runtime_game import DBRuntimeGame
from models.types import PyObjectId
from repositories.base_repository import BaseRepository, BaseMockRepository
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class RuntimeGameRepository(BaseRepository[DBRuntimeGame]):
    """运行时游戏数据仓库的MongoDB实现，处理所有运行时游戏相关的数据库操作"""

    def __init__(self, collection: AsyncIOMotorCollection): # type: ignore
        self.collection = collection

    async def create(self, game: DBRuntimeGame) -> Optional[DBRuntimeGame]:
        """创建新运行时游戏"""
        try:
            result = await self.collection.insert_one(game.model_dump(by_alias=True))
            game.id = result.inserted_id
            return game
        except Exception as e:
            logger.error(f"Failed to create runtime game: {str(e)}")
            return None

    async def get(self, id: PyObjectId) -> Optional[DBRuntimeGame]:
        """获取运行时游戏数据"""
        try:
            game_data = await self.collection.find_one({"_id": id})
            if game_data:
                return DBRuntimeGame.model_validate(game_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get runtime game: {str(e)}")
            return None

    async def list(self, filter_dict: Dict[str, Any] = None) -> List[DBRuntimeGame]:
        """获取运行时游戏列表"""
        try:
            filter_dict = filter_dict or {}
            cursor = self.collection.find(filter_dict)
            games = []
            async for game_data in cursor:
                games.append(DBRuntimeGame.model_validate(game_data))
            return games
        except Exception as e:
            logger.error(f"Failed to list runtime games: {str(e)}")
            return []

    async def update(self, id: PyObjectId, fields: Dict[str, Any]) -> bool:
        """
        更新运行时游戏字段
        
        Example:
            # 更新进度
            await repo.update(id, {
                "progress": progress
            })
            
            # 更新章节信息
            await repo.update(id, {
                "chapters": chapters
            })
            
            # 更新游戏状态
            await repo.update(id, {
                "status": "completed",
                "error": None
            })
        """
        try:
            update_data = {}
            for field_name, field_value in fields.items():
                if hasattr(field_value, "model_dump"):
                    update_data[field_name] = field_value.model_dump()
                elif isinstance(field_value, list) and all(hasattr(item, "model_dump") for item in field_value):
                    update_data[field_name] = [item.model_dump() for item in field_value]
                else:
                    update_data[field_name] = field_value

            result = await self.collection.update_one(
                {"_id": id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update runtime game: {str(e)}")
            return False

    async def delete(self, id: PyObjectId) -> bool:
        """删除运行时游戏"""
        try:
            result = await self.collection.delete_one({"_id": id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete runtime game: {str(e)}")
            return False


class MockRuntimeGameRepository(BaseMockRepository[DBRuntimeGame]):
    """用于测试的运行时游戏数据仓库实现"""
    
    async def create(self, game: DBRuntimeGame) -> bool:
        """创建运行时游戏"""
        if not game.id:
            game.id = PyObjectId()
        return await super().create(game) 