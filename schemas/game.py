from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from models.game import DBGame, GameStatus

class GameListItemSchema(BaseModel):
    """游戏列表项响应模型"""
    id: str
    runtime_id: Optional[str] = None
    title: str
    cover_image: Optional[str] = None
    status: str = Field(description="游戏状态: generating, published, failed")
    progress: float = Field(description="生成进度, 0-100", ge=0, le=100)
    current_chapter: int = Field(description="当前章节数")
    chapter_count: int = Field(description="章节数量")
    created_at: datetime

    @classmethod
    def from_db_game(cls, game: DBGame) -> "GameListItemSchema":
        """从数据库模型转换为响应模型"""
        progress = game.progress.progress
        
        # 转换状态
        status_map = {
            GameStatus.GENERATING: "generating",
            GameStatus.COMPLETED: "published",
            GameStatus.FAILED: "failed"
        }
        
        return cls(
            id=str(game.id),
            runtime_id=str(game.runtime_id) if game.runtime_id else None,
            title=game.title,
            cover_image=game.settings.get("cover_image"),
            status=status_map[game.status],
            progress=progress,
            current_chapter=game.generate_chapter_index,
            chapter_count=len(game.chapters),
            created_at=game.created_at,
        )
