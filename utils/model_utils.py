from typing import Any
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel
from models.types import PyObjectId
from enum import Enum

def model_to_json(obj: Any) -> Any:
    """将 Pydantic 模型或其他类型转换为 JSON 可序列化对象
    
    支持以下类型的转换:
    - Pydantic 模型
    - ObjectId/PyObjectId -> str
    - datetime -> ISO 格式字符串
    - Enum -> 值
    - List -> 列表中的每个元素都会被转换
    - Dict -> 字典中的每个值都会被转换
    
    Args:
        obj: 要转换的对象
        
    Returns:
        转换后的 JSON 可序列化对象
    """
    if isinstance(obj, BaseModel):
        # 使用 mode='json' 来避免序列化警告
        return model_to_json(obj.model_dump(mode='json'))
    elif isinstance(obj, (ObjectId, PyObjectId)):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, list):
        return [model_to_json(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: model_to_json(value) for key, value in obj.items()}
    elif obj is None:
        return None
    return obj
