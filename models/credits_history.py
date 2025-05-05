from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from models.types import PyObjectId

class DBCreditsHistory(BaseModel):
    """积分历史记录模型"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: PyObjectId
    amount: int
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        populate_by_name = True
