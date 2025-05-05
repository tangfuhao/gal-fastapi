from typing import TypeVar, Generic, Dict, Any, Optional, List
from pydantic import BaseModel
from abc import ABC, abstractmethod
from models.types import PyObjectId

T = TypeVar('T', bound=BaseModel)

class BaseRepository(ABC, Generic[T]):
    """通用的仓库基类，定义了基本的CRUD操作接口"""

    @abstractmethod
    async def create(self, model: T) -> Optional[T]:
        """
        创建新记录
        
        Args:
            model: 数据模型对象
            
        Returns:
            bool: 创建是否成功
        """
        pass

    @abstractmethod
    async def get(self, id: PyObjectId) -> Optional[T]:
        """
        获取单条记录
        
        Args:
            id: 记录ID
            
        Returns:
            Optional[T]: 数据模型对象，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def list(self, filter_dict: Dict[str, Any] = None) -> List[T]:
        """
        获取记录列表
        
        Args:
            filter_dict: 过滤条件字典
            
        Returns:
            List[T]: 数据模型对象列表
        """
        pass

    @abstractmethod
    async def update(self, id: PyObjectId, fields: Dict[str, Any]) -> bool:
        """
        更新记录
        
        Args:
            id: 记录ID
            fields: 要更新的字段字典
            
        Returns:
            bool: 更新是否成功
        """
        pass

    @abstractmethod
    async def delete(self, id: PyObjectId) -> bool:
        """
        删除记录
        
        Args:
            id: 记录ID
            
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    async def find_many(
        self,
        filter_dict: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 20,
        sort: Dict[str, Any] = None
    ) -> List[T]:
        pass


class BaseMockRepository(BaseRepository[T]):
    """通用的Mock仓库实现，用于测试"""

    def __init__(self):
        self.data: Dict[PyObjectId, T] = {}

    async def create(self, model: T) -> bool:
        """创建新记录"""
        if model.id not in self.data:
            self.data[model.id] = model
            return True
        return False

    async def get(self, id: PyObjectId) -> Optional[T]:
        """获取单条记录"""
        return self.data.get(id)

    async def list(self, filter_dict: Dict[str, Any] = None) -> List[T]:
        """获取记录列表"""
        if not filter_dict:
            return list(self.data.values())
        
        filtered_items = []
        for item in self.data.values():
            match = True
            for key, value in filter_dict.items():
                if getattr(item, key, None) != value:
                    match = False
                    break
            if match:
                filtered_items.append(item)
        return filtered_items

    async def update(self, id: PyObjectId, fields: Dict[str, Any]) -> bool:
        """更新记录"""
        if id not in self.data:
            return False
        
        item = self.data[id]
        for field_name, field_value in fields.items():
            setattr(item, field_name, field_value)
        return True

    async def delete(self, id: PyObjectId) -> bool:
        """删除记录"""
        if id in self.data:
            del self.data[id]
            return True
        return False
