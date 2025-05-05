from typing import Optional, Set
from datetime import datetime
from pydantic import BaseModel, Field
from models.db_runtime_game import DBRuntimeGame

class GameListItemSchema(BaseModel):
    """游戏列表项响应模型"""
    id: str = Field(..., description="游戏ID")
    title: str = Field(..., max_length=100, description="游戏标题")
    cover_image: Optional[str] = Field(default=None, description="封面图片URL")
    description: Optional[str] = Field(default=None, max_length=500, description="游戏描述")
    user_name: str = Field(..., min_length=1, max_length=50, description="作者名称")
    user_avatar: Optional[str] = Field(default=None, description="作者头像")
    tags: Set[str] = Field(default_factory=set, description="游戏标签")
    play_count: int = Field(default=0, ge=0, description="游戏游玩次数")
    like_count: int = Field(default=0, ge=0, description="游戏点赞数")
    comment_count: int = Field(default=0, ge=0, description="游戏评论数")
    published_at: Optional[datetime] = Field(default=None, description="发布时间")

    @classmethod
    def from_db_runtime_game(cls, game: DBRuntimeGame) -> "GameListItemSchema":
        """从数据库游戏对象创建响应模型"""
        return cls(
            id=str(game.id),
            title=game.title or "",
            cover_image=game.cover_image,
            description=game.description,
            user_name=game.user_info.name,
            user_avatar=game.user_info.avatar_url,
            tags=game.tags,
            play_count=game.play_count,
            like_count=game.like_count,
            comment_count=game.comment_count,
            published_at=game.published_at
        )
