from datetime import datetime
from pydantic import BaseModel

class AdminUserListItem(BaseModel):
    """管理员视图的用户列表项"""
    id: str
    name: str
    email: str
    avatar: str
    is_admin: bool
    created_at: datetime
