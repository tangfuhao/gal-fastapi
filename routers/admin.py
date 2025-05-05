from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorCollection
from math import ceil

from models.user import DBUser
from models.types import PyObjectId
from models.credits import DBCredits, DBCreditsHistory
from schemas.credits import CreditsResponse
from schemas.admin.credits import AdminUpdateCreditsRequest
from schemas.admin.user import AdminUserListItem
from schemas.common import PaginatedResponse, PaginationParams
from core.auth import get_current_user
from repositories.base_repository import BaseRepository
from core.container import get_user_repository, get_credits_repository, get_credits_history_repository
from constant.credits import INITIAL_CREDITS

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])

async def get_admin_user(current_user: DBUser = Depends(get_current_user)) -> DBUser:
    """验证当前用户是否为管理员"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can perform this operation"
        )
    return current_user

@admin_router.get("/users", response_model=PaginatedResponse[AdminUserListItem])
async def list_users(
    pagination: PaginationParams = Depends(),
    admin: DBUser = Depends(get_admin_user),
    user_repo: BaseRepository[DBUser] = Depends(get_user_repository)
):
    """
    获取用户列表（分页）
    """
    # 计算跳过的文档数
    skip = (pagination.page - 1) * pagination.page_size

    # 获取用户列表
    users = await user_repo.find_many(
        filter_dict={},
        skip=skip,
        limit=pagination.page_size,
        sort={"created_at": -1}
    )
    
    # 转换为响应模型
    user_items = [
        AdminUserListItem(
            id=str(user.id),
            name=user.name,
            email=user.email,
            avatar=user.avatar or "",
            is_admin=user.is_admin or False,
            created_at=user.created_at
        ) for user in users
    ]
    
    # 获取总文档数并计算总页数
    total = len(await user_repo.list({}))
    total_pages = ceil(total / pagination.page_size)
    
    return PaginatedResponse(
        items=user_items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages
    )

@admin_router.post("/user/{user_id}/credits", response_model=CreditsResponse)
async def update_user_credits(
    user_id: str,
    request: AdminUpdateCreditsRequest,
    admin: DBUser = Depends(get_admin_user),
    credits_repo: BaseRepository[DBCredits] = Depends(get_credits_repository),
    credits_history_repo: BaseRepository[DBCreditsHistory] = Depends(get_credits_history_repository)
):
    """
    管理员更新用户积分（增加或减少）
    """
    user_object_id = PyObjectId(user_id)
    
    # 获取当前积分
    credits = await credits_repo.find_many({"user_id": user_object_id})
    if not credits:
        # 如果没有积分记录，创建一个初始积分记录
        initial_credits = DBCredits(
            user_id=user_object_id,
            amount=INITIAL_CREDITS
        )
        credits = await credits_repo.create(initial_credits)
    else:
        credits = credits[0]  # 获取第一个匹配的记录
    
    # 计算新的积分值
    new_amount = credits.amount + request.amount
    if new_amount < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient credits"
        )
    
    # 更新积分
    now = datetime.utcnow()
    await credits_repo.update(credits.id, {
        "amount": new_amount,
        "updated_at": now
    })
    
    # 记录积分历史
    history = DBCreditsHistory(
        user_id=user_object_id,
        amount=request.amount,
        reason=f"[Admin: {admin.name}] {request.reason}"
    )
    await credits_history_repo.create(history)
    
    return CreditsResponse(credits=new_amount, updated_at=now)
