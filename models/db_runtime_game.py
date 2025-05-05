from datetime import datetime
from typing import List, Optional, Set, Dict, Any
from pydantic import BaseModel, Field
from models.types import PyObjectId
from models.game import DBGame
from utils.script_coder import parse_script
from dataclasses import asdict
from bson import ObjectId
import json

class DBGameCommand(BaseModel):
    """数据库中的游戏命令"""
    type: str = Field(..., description="命令类型")
    name: Optional[str] = Field(default=None, description="命令名称")
    text: Optional[str] = Field(default=None, description="命令文本")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="命令元数据")

class DBRuntimeBranch(BaseModel):
    """数据库中的游戏分支"""
    name: str = Field(..., min_length=1, max_length=100, description="分支名称")
    commands: List[DBGameCommand] = Field(..., description="脚本指令列表")

class DBRuntimeCharacterImage(BaseModel):
    """数据库中的角色立绘"""
    name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    oss_url: str = Field(..., description="立绘图片URL")

class DBRuntimeChapter(BaseModel):
    """数据库中的游戏章节"""
    id: str = Field(..., description="章节ID")
    index: int = Field(..., ge=0, description="章节序号")
    title: str = Field(..., min_length=1, max_length=100, description="章节标题")
    branches: List[DBRuntimeBranch] = Field(default_factory=list, description="游戏分支列表")
    characters: List[DBRuntimeCharacterImage] = Field(default_factory=list, description="章节涉及的角色立绘")

class DBRuntimeUserInfo(BaseModel):
    """用户信息"""
    name: str = Field(..., min_length=1, max_length=50, description="用户名称")
    avatar_url: Optional[str] = Field(default=None, description="用户头像URL")

class DBRuntimeGame(BaseModel):
    """数据库中的运行时游戏模型"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id", description="游戏ID")
    title: Optional[str] = Field(default=None, max_length=100, description="游戏标题")
    cover_image: Optional[str] = Field(default=None, description="封面图片URL")
    description: Optional[str] = Field(default=None, max_length=500, description="游戏描述")
    user_id: PyObjectId = Field(..., description="作者ID")
    user_info: DBRuntimeUserInfo = Field(..., description="作者信息")
    version: Optional[str] = Field(default="1.0.0", description="游戏版本")
    total_chapters: int = Field(..., ge=0, description="总章节数")
    chapters: List[DBRuntimeChapter] = Field(default_factory=list, description="章节列表")
    tags: Set[str] = Field(default_factory=set, description="游戏标签")
    play_count: int = Field(default=0, ge=0, description="游戏游玩次数")
    like_count: int = Field(default=0, ge=0, description="游戏点赞数")
    comment_count: int = Field(default=0, ge=0, description="游戏评论数")
    is_published: bool = Field(default=False, description="是否已发布")
    published_at: Optional[datetime] = Field(default=None, description="发布时间")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    deleted_at: Optional[datetime] = Field(default=None, description="删除时间")
    is_deleted: bool = Field(default=False, description="是否已删除")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="游戏元数据")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
        populate_by_name = True

    @classmethod
    def convert_to_runtime_game(cls, game: DBGame) -> "DBRuntimeGame":
        """
        将DBGame转换为DBRuntimeGame
        
        Args:
            game: 数据库游戏对象
            
        Returns:
            DBRuntimeGame: 运行时游戏对象
        """
        # 处理章节，只包含已生成的章节
        runtime_chapters = []
        for chapter in game.chapters:
            # 跳过未生成的章节
            if chapter.index >= game.generate_chapter_index:
                continue
                
            commands = chapter.branches
                
            # 构建分支
            branch = DBRuntimeBranch(
                name="main",
                commands=[
                    DBGameCommand(
                        type=cmd.__class__.__name__,
                        name=getattr(cmd, "name", None),
                        text=getattr(cmd, "text", None),
                        metadata=asdict(cmd)
                    ) for cmd in commands
                ]
            )
            
            # 构建章节
            runtime_chapter = DBRuntimeChapter(
                id=str(chapter.id),
                index=chapter.index,
                title=chapter.title or f"第{chapter.index + 1}章",
                branches=[branch],
                characters=[]  # 角色立绘会在后续处理中添加
            )
            runtime_chapters.append(runtime_chapter)
        
        # 创建运行时游戏
        runtime_game = cls(
            id=game.id,
            title=game.title,
            user_id=game.user_id,
            user_info=DBRuntimeUserInfo(
                name=game.user_info.name,
                avatar_url=game.user_info.avatar_url
            ),
            total_chapters=len(runtime_chapters),
            chapters=runtime_chapters,
            metadata={
                "original_game_id": str(game.id),
                "input_text_type": game.input_text_type,
                "settings": game.settings
            }
        )
        
        return runtime_game
