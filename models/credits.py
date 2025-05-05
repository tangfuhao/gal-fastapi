from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId
from models.types import PyObjectId

class DBCredits(BaseModel):
    """用户积分模型"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id", description="积分记录ID")
    user_id: PyObjectId = Field(..., description="用户ID")
    amount: int = Field(default=0, ge=0, description="当前积分数量")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="最后更新时间")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
        populate_by_name = True

    @field_validator("amount")
    def validate_amount(cls, v: int) -> int:
        """验证积分数量不能为负数"""
        if v < 0:
            raise ValueError("积分不能为负数")
        return v

class DBCreditsHistory(BaseModel):
    """用户积分变更历史记录"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id", description="历史记录ID")
    user_id: PyObjectId = Field(..., description="用户ID")
    amount: int = Field(..., description="变更数量（正数表示增加，负数表示减少）")
    reason: str = Field(..., min_length=1, max_length=200, description="变更原因")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
        populate_by_name = True
