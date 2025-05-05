from datetime import datetime
from typing import List, Optional, Set, Dict, Any
from pydantic import BaseModel, Field
from models.user import DBUser
from models.types import PyObjectId
from models.db_runtime_game import DBRuntimeGame
import logging
from models.db_runtime_game import DBRuntimeBranch

logger = logging.getLogger(__name__)

class GameCharacterImageSchema(BaseModel):
    """角色立绘"""
    name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    oss_url: str = Field(..., description="立绘图片URL")

class GameCommandSchema(BaseModel):
    """游戏命令响应模型"""
    type: str = Field(..., description="命令类型")
    name: Optional[str] = Field(default=None, description="命令名称")
    content: Optional[str] = Field(default=None, description="命令文本")
    is_target_protagonist: Optional[bool] = Field(default=False, description="是否为目标主角")
    oss_url: Optional[str] = Field(default=None, description="命令关联的资源URL")

class GameBranchSchema(BaseModel):
    """游戏分支响应模型"""
    name: str = Field(..., min_length=1, max_length=100, description="分支名称")
    commands: List[GameCommandSchema] = Field(..., description="脚本指令列表")

class GameChapterSchema(BaseModel):
    """游戏章节响应模型"""
    id: str = Field(..., description="章节ID")
    index: int = Field(..., ge=0, description="章节序号")
    title: str = Field(..., min_length=1, max_length=100, description="章节标题")
    branches: List[GameBranchSchema] = Field(default_factory=list, description="游戏分支列表")
    characters: List[GameCharacterImageSchema] = Field(default_factory=list, description="章节涉及的角色立绘")

class GameRuntimeSchema(BaseModel):
    """游戏运行时响应模型"""
    id: str = Field(..., description="游戏ID")
    title: Optional[str] = Field(default=None, max_length=100, description="游戏标题")
    cover_image: Optional[str] = Field(default=None, description="封面图片URL")
    description: Optional[str] = Field(default=None, max_length=500, description="游戏描述")
    user_id: str = Field(..., description="作者ID")
    user_name: str = Field(..., min_length=1, max_length=50, description="作者名称")
    user_avatar: Optional[str] = Field(default=None, description="作者头像")
    version: Optional[str] = Field(default="1.0.0", description="游戏版本")
    total_chapters: int = Field(..., ge=0, description="总章节数")
    chapters: List[GameChapterSchema] = Field(default_factory=list, description="章节列表")
    tags: Set[str] = Field(default_factory=set, description="游戏标签")
    play_count: int = Field(default=0, ge=0, description="游戏游玩次数")
    like_count: int = Field(default=0, ge=0, description="游戏点赞数")
    comment_count: int = Field(default=0, ge=0, description="游戏评论数")
    is_published: bool = Field(default=False, description="是否已发布")
    published_at: Optional[datetime] = Field(default=None, description="发布时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="游戏元数据")

    class Config:
        json_encoders = {
            GameBranchSchema: lambda b: {"name": b.name, "commands": [c.__dict__ for c in b.commands]},
            GameCommandSchema: lambda c: c.__dict__,
            datetime: lambda dt: dt.isoformat()
        }

    @staticmethod
    def _convert_character_images(characters) -> List[GameCharacterImageSchema]:
        """转换角色立绘列表"""
        try:
            return [
                GameCharacterImageSchema(
                    name=character.name,
                    oss_url=character.oss_url
                )
                for character in characters
            ]
        except Exception as e:
            logger.error(f"Failed to convert character images: {str(e)}")
            return []

    @staticmethod
    def _convert_game_branch(branch: DBRuntimeBranch) -> GameBranchSchema:
        """转换游戏分支"""
        try:
            return GameBranchSchema(
                name=branch.name,
                commands=[
                    GameCommandSchema(
                        type=cmd.type,
                        name=cmd.name,
                        content=cmd.content,
                        is_target_protagonist=cmd.is_target_protagonist,
                        oss_url=cmd.oss_url
                    )
                    for cmd in branch.commands
                ]
            )
        except Exception as e:
            logger.error(f"Failed to convert game branch: {str(e)}")
            return GameBranchSchema(name="error", commands=[])

    @staticmethod
    def _convert_game_chapter(chapter) -> GameChapterSchema:
        """转换游戏章节"""
        try:
            return GameChapterSchema(
                id=chapter.id,
                index=chapter.index,
                title=chapter.title,
                branches=[
                    GameRuntimeSchema._convert_game_branch(branch)
                    for branch in chapter.branches
                ],
                characters=GameRuntimeSchema._convert_character_images(chapter.characters)
            )
        except Exception as e:
            logger.error(f"Failed to convert game chapter: {str(e)}")
            return GameChapterSchema(
                id="error",
                index=0,
                title="Error converting chapter",
                branches=[],
                characters=[]
            )

    @classmethod
    def from_db_runtime_game(cls, db_game: DBRuntimeGame) -> "GameRuntimeSchema":
        """从数据库模型创建响应模型"""
        return cls(
            id=str(db_game.id),
            title=db_game.title,
            cover_image=db_game.cover_image,
            description=db_game.description,
            user_id=str(db_game.user_id),
            user_name=db_game.user_info.name,
            user_avatar=db_game.user_info.avatar_url,
            version=db_game.version,
            total_chapters=db_game.total_chapters,
            chapters=[
                cls._convert_game_chapter(chapter)
                for chapter in db_game.chapters
            ],
            tags=db_game.tags,
            play_count=db_game.play_count,
            like_count=db_game.like_count,
            comment_count=db_game.comment_count,
            is_published=db_game.is_published,
            published_at=db_game.published_at,
            created_at=db_game.created_at,
            updated_at=db_game.updated_at,
            metadata=db_game.metadata
        )
