from motor.motor_asyncio import AsyncIOMotorCollection
from models.user import DBUser  # 假设有这个模型
from repositories.base_repository import BaseRepository, BaseMockRepository
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class UserRepository(BaseRepository[DBUser]):
    """用户数据仓库的具体实现，处理所有用户相关的数据库操作"""

    def __init__(self, collection: AsyncIOMotorCollection): # type: ignore
        self.collection = collection

    async def create(self, model: DBUser) -> Optional[DBUser]:
        """创建新用户"""
        try:
            result = await self.collection.insert_one(model.model_dump(by_alias=True))
            model.id = result.inserted_id
            return model
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            return None

    async def get(self, id: str) -> Optional[DBUser]:
        """获取用户数据"""
        try:
            user_data = await self.collection.find_one({"_id": id})
            if user_data:
                return DBUser.model_validate(user_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get user: {str(e)}")
            return None

    async def list(self, filter_dict: Dict[str, Any] = None) -> List[DBUser]:
        """获取用户列表"""
        try:
            filter_dict = filter_dict or {}
            cursor = self.collection.find(filter_dict)
            users = []
            async for user_data in cursor:
                users.append(DBUser.model_validate(user_data))
            return users
        except Exception as e:
            logger.error(f"Failed to list users: {str(e)}")
            return []

    async def update(self, id: str, fields: Dict[str, Any]) -> bool:
        """更新用户数据"""
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
            logger.error(f"Failed to update user: {str(e)}")
            return False

    async def delete(self, id: str) -> bool:
        """删除用户"""
        try:
            result = await self.collection.delete_one({"_id": id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete user: {str(e)}")
            return False

    # 用户特有的方法
    async def get_by_email(self, email: str) -> Optional[DBUser]:
        """通过邮箱获取用户"""
        try:
            user_data = await self.collection.find_one({"email": email})
            if user_data:
                return DBUser.model_validate(user_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get user by email: {str(e)}")
            return None

    async def update_last_login(self, id: str) -> bool:
        """更新用户最后登录时间"""
        try:
            from datetime import datetime
            result = await self.collection.update_one(
                {"_id": id},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update user last login: {str(e)}")
            return False


class MockUserRepository(BaseMockRepository[DBUser]):
    """用于测试的用户数据仓库实现"""

    async def get_by_email(self, email: str) -> Optional[DBUser]:
        """通过邮箱获取用户"""
        for user in self.data.values():
            if user.email == email:
                return user
        return None

    async def update_last_login(self, id: str) -> bool:
        """更新用户最后登录时间"""
        if id in self.data:
            from datetime import datetime
            self.data[id].last_login = datetime.utcnow()
            return True
        return False
