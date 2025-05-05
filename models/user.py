from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from models.types import PyObjectId

class DBUser(BaseModel):
    """数据库中的用户模型"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id", description="用户ID")
    google_id: str = Field(..., description="Google OAuth ID")
    name: str = Field(..., min_length=1, max_length=50, description="用户名称")
    email: EmailStr = Field(..., description="邮箱地址")
    avatar: str = Field(default="", description="头像URL")
    is_admin: bool = Field(default=False, description="是否为管理员")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
        populate_by_name = True
