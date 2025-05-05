from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status

from models.user import DBUser
from models.game import DBGame
from models.types import PyObjectId
from models.credits import DBCredits, DBCreditsHistory
from schemas.game import GameListItemSchema
from schemas.credits import CreditsResponse, CreditsHistoryResponse
from core.auth import get_current_user
from repositories.base_repository import BaseRepository
from core.container import (
    get_game_repository,
    get_runtime_game_repository,
    get_credits_repository,
    get_credits_history_repository
)
from constant.credits import INITIAL_CREDITS

user_router = APIRouter(prefix="/api/user", tags=["user"])

@user_router.get("/me/games", response_model=List[GameListItemSchema])
async def get_user_games(
    current_user: DBUser = Depends(get_current_user),
    game_repo: BaseRepository[DBGame] = Depends(get_game_repository)
):
    """
    获取当前用户的游戏列表（不包含已删除的游戏）
    
    Returns:
        游戏列表，按创建时间倒序排序
    """
    games = await game_repo.find_many(
        filter_dict={
            "user_id": current_user.id,
            "is_deleted": {"$ne": True}
        },
        sort={"created_at": -1}
    )
    
    return [GameListItemSchema.from_db_game(game) for game in games]

@user_router.delete("/me/games/{game_id}", response_model=dict)
async def delete_user_game(
    game_id: str,
    current_user: DBUser = Depends(get_current_user),
    game_repo: BaseRepository[DBGame] = Depends(get_game_repository),
    runtime_repo: BaseRepository[DBGame] = Depends(get_runtime_game_repository)
):
    """
    删除用户的游戏（逻辑删除）
    
    Args:
        game_id: 游戏ID
        
    Returns:
        删除成功的消息
        
    Raises:
        404: 游戏不存在
        403: 无权删除该游戏
        400: 删除失败
    """
    try:
        # 转换game_id为PyObjectId
        game_id = PyObjectId(game_id)
        
        # 查找游戏
        games = await game_repo.find_many({
            "_id": game_id,
            "is_deleted": {"$ne": True}  # 确保游戏未被删除
        })
        
        if not games:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found or already deleted"
            )
        
        game = games[0]
        if str(game.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this game"
            )
            
        # 更新游戏状态为已删除
        current_time = datetime.utcnow()
        updated = await game_repo.update(game_id, {
            "is_deleted": True,
            "updated_at": current_time,
            "deleted_at": current_time
        })
        
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete game"
            )
        
        # 如果存在运行时游戏，也标记为删除
        if game.runtime_id:
            await runtime_repo.update(game.runtime_id, {
                "is_deleted": True,
                "updated_at": current_time,
                "deleted_at": current_time
            })
        
        return {
            "message": "Game deleted successfully",
            "game_id": str(game_id),
            "runtime_id": str(game.runtime_id) if game.runtime_id else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@user_router.get("/credits", response_model=CreditsResponse)
async def get_user_credits(
    current_user: DBUser = Depends(get_current_user),
    credits_repo: BaseRepository[DBCredits] = Depends(get_credits_repository)
):
    """
    获取当前用户的积分
    """
    credits = await credits_repo.find_many({"user_id": current_user.id})
    
    if not credits:
        # 如果没有积分记录，创建一个初始积分记录
        initial_credits = DBCredits(
            user_id=current_user.id,
            amount=INITIAL_CREDITS
        )
        credits = await credits_repo.create(initial_credits)
    else:
        credits = credits[0]
    
    return CreditsResponse(
        credits=credits.amount,
        updated_at=credits.updated_at
    )

@user_router.get("/credits/history", response_model=List[CreditsHistoryResponse])
async def get_credits_history(
    current_user: DBUser = Depends(get_current_user),
    credits_history_repo: BaseRepository[DBCreditsHistory] = Depends(get_credits_history_repository)
):
    """
    获取用户积分变更历史
    """
    history = await credits_history_repo.find_many(
        filter_dict={"user_id": current_user.id},
        sort={"created_at": -1}  # 按时间倒序
    )
    
    return [
        CreditsHistoryResponse(
            amount=item.amount,
            reason=item.reason,
            created_at=item.created_at
        ) for item in history
    ]
