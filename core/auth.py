from fastapi import Depends, HTTPException, Header, status
from typing import Optional
from models.user import DBUser
from repositories.base_repository import BaseRepository
from core.container import get_user_repository
from utils.jwt import get_current_user_id
from models.types import PyObjectId

async def get_current_user(
    authorization: Optional[str] = Header(None),
    user_repo: BaseRepository[DBUser] = Depends(get_user_repository)
) -> Optional[DBUser]:
    """
    从 Authorization header 中获取当前用户。
    如果没有提供 token 或 token 无效，返回 None。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split(" ")[1]
    try:
        user_id = get_current_user_id(token)
        # 转换为 ObjectId
        user_id = PyObjectId(user_id)
        user = await user_repo.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
