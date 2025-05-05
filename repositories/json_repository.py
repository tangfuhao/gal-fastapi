import json
import os
from typing import Dict, Any, Optional, List, TypeVar, Generic
from pydantic import BaseModel
import logging
from models.types import PyObjectId
import glob
from utils.model_utils import model_to_json

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class JsonRepository(Generic[T]):
    """基于JSON文件的本地存储仓库实现，每个实体保存为单独的文件"""

    def __init__(self, directory_path: str, model_class: type[T]):
        """
        初始化JSON仓库
        
        Args:
            directory_path: JSON文件目录路径
            model_class: 数据模型类
        """
        self.directory_path = directory_path
        self.model_class = model_class
        self._ensure_directory_exists()

    def _ensure_directory_exists(self):
        """确保存储目录存在"""
        os.makedirs(self.directory_path, exist_ok=True)

    def _get_file_path(self, id: PyObjectId) -> str:
        """获取实体的JSON文件路径"""
        return os.path.join(self.directory_path, f"{str(id)}.json")

    def _load_item(self, file_path: str) -> Optional[T]:
        """从JSON文件加载单个实体"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                item_data = json.load(f)
                # 直接使用模型类的 model_validate 方法
                return self.model_class.model_validate(item_data)
        except Exception as e:
            logger.error(f"加载JSON数据失败 {file_path}: {str(e)}")
            return None

    def _save_item(self, model: T) -> bool:
        """保存单个实体到JSON文件"""
        try:
            # 使用工具函数转换为JSON可序列化对象
            item_dict = model.model_dump(mode='json')
            file_path = self._get_file_path(model.id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(item_dict, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存JSON数据失败: {str(e)}")
            return False

    async def create(self, model: T) -> Optional[T]:
        """创建新记录"""
        file_path = self._get_file_path(model.id)
        if not os.path.exists(file_path):
            return self._save_item(model)
        return model

    async def get(self, id: PyObjectId) -> Optional[T]:
        """获取单条记录"""
        file_path = self._get_file_path(id)
        if os.path.exists(file_path):
            return self._load_item(file_path)
        return None

    async def list(self, filter_dict: Dict[str, Any] = None) -> List[T]:
        """获取记录列表"""
        items = []
        for file_path in glob.glob(os.path.join(self.directory_path, "*.json")):
            item = self._load_item(file_path)
            if item:
                if not filter_dict:
                    items.append(item)
                else:
                    match = True
                    for key, value in filter_dict.items():
                        if getattr(item, key, None) != value:
                            match = False
                            break
                    if match:
                        items.append(item)
        return items

    async def update(self, id: PyObjectId, fields: Dict[str, Any]) -> bool:
        """更新记录"""
        item = await self.get(id)
        if not item:
            return False
        
        for field_name, field_value in fields.items():
            setattr(item, field_name, field_value)
        return self._save_item(item)

    async def delete(self, id: PyObjectId) -> bool:
        """删除记录"""
        file_path = self._get_file_path(id)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except Exception as e:
                logger.error(f"删除文件失败 {file_path}: {str(e)}")
        return False
