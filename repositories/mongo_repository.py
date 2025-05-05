from typing import TypeVar, Generic, Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel
from models.types import PyObjectId
from .base_repository import BaseRepository
import logging
import enum

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class MongoRepository(BaseRepository[T], Generic[T]):
    """MongoDB仓库实现，支持错误处理和复杂对象序列化"""
    
    def __init__(self, collection: AsyncIOMotorCollection, model_class: type[T]):
        self.collection = collection
        self.model_class = model_class

    async def create(self, model: T) -> Optional[T]:
        """创建新记录"""
        try:
            result = await self.collection.insert_one(model.model_dump(exclude_none=True, by_alias=True))
            if result.inserted_id:
                return await self.get(result.inserted_id)
            return None
        except Exception as e:
            logger.error(f"Failed to create document: {str(e)}")
            return None

    async def get(self, id: PyObjectId) -> Optional[T]:
        """获取单条记录"""
        try:
            doc = await self.collection.find_one({"_id": id})
            if doc:
                return self.model_class.model_validate(doc)
            return None
        except Exception as e:
            logger.error(f"Failed to get document: {str(e)}")
            return None

    async def list(self, filter_dict: Dict[str, Any] = None) -> List[T]:
        """获取记录列表"""
        try:
            cursor = self.collection.find(filter_dict or {})
            docs = await cursor.to_list(length=None)
            return [self.model_class.model_validate(doc) for doc in docs]
        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}")
            return []

    def _prepare_update_data(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """准备更新数据，处理嵌套的Pydantic模型和枚举类型"""
        def process_value(value: Any) -> Any:
            if hasattr(value, "model_dump"):
                return value.model_dump()
            elif isinstance(value, list):
                return [process_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: process_value(v) for k, v in value.items()}
            elif isinstance(value, enum.Enum):
                return value.value
            else:
                return value

        update_data = {}
        for field_name, field_value in fields.items():
            update_data[field_name] = process_value(field_value)
        return update_data

    async def update(self, id: PyObjectId, fields: Dict[str, Any]) -> bool:
        """
        更新记录
        
        支持更新:
        - 普通字段值
        - Pydantic模型 (自动调用model_dump)
        - Pydantic模型列表 (自动调用每个元素的model_dump)
        """
        try:
            update_data = self._prepare_update_data(fields)
            result = await self.collection.update_one(
                {"_id": id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update document: {str(e)}")
            return False

    async def delete(self, id: PyObjectId) -> bool:
        """删除记录"""
        try:
            result = await self.collection.delete_one({"_id": id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete document: {str(e)}")
            return False

    async def find_many(
        self,
        filter_dict: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 20,
        sort: Dict[str, Any] = None
    ) -> List[T]:
        """
        获取多条记录，支持分页和排序
        
        Args:
            filter_dict: 过滤条件
            skip: 跳过记录数
            limit: 返回记录数限制
            sort: 排序条件，例如 {"created_at": -1}
        """
        try:
            cursor = self.collection.find(filter_dict or {})
            
            if sort:
                cursor = cursor.sort(list(sort.items()))
                
            cursor = cursor.skip(skip).limit(limit)
            docs = await cursor.to_list(length=None)
            return [self.model_class.model_validate(doc) for doc in docs]
        except Exception as e:
            logger.error(f"Failed to find documents: {str(e)}")
            return []
