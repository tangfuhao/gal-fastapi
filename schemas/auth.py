from typing import Optional
from pydantic import BaseModel
from models.user import DBUser

class UserResponseSchema(BaseModel):
    """用户信息响应模型"""
    id: str
    username: str
    email: str
    avatar_url: str

    @classmethod
    def from_db_user(cls, db_user: DBUser) -> "UserResponseSchema":
        """从数据库用户模型创建响应模型"""
        return cls(
            id=str(db_user.id),
            username=db_user.name,
            email=db_user.email,
            avatar_url=db_user.avatar
        )

class AuthStatusResponseSchema(BaseModel):
    """认证状态响应模型"""
    isLoggedIn: bool
    user: Optional[UserResponseSchema] = None
