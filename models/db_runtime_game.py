from datetime import datetime
from typing import List, Optional, Set, Dict, Any, Iterator
from pydantic import BaseModel, Field
from starlette.responses import Content
from models.types import PyObjectId
from models.game import DBGame
from utils.script_coder import parse_script
from dataclasses import asdict
from bson import ObjectId
from schemas.script_commands import (
    CommandType,
    BaseCommand,
    NarrationCommand,
    DialogueCommand,
    ChoiceCommand,
    JumpCommand,
    BackgroundCommand,
    BGMCommand,
    Branch,
    Command,
    ScriptValidationError,
    BranchError,
    CommandError,
    StructureError
)
import json

class DBGameCommand(BaseModel):
    """数据库中的游戏命令"""
    type: str = Field(..., description="命令类型")
    name: Optional[str] = Field(default=None, description="命令名称")
    content: Optional[str] = Field(default=None, description="命令文本")
    is_target_protagonist: Optional[bool] = Field(default=None, description="是否为目标主角")
    oss_url: Optional[str] = Field(default=None, description="立绘图片URL")

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
    tags: List[str] = Field(default_factory=list, description="游戏标签")
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
    def _get_command_type(cls, cmd: Command) -> str:
        """获取命令类型
        
        Args:
            cmd: 原始命令
            
        Returns:
            str: 命令类型
        """
        return cmd.type.value

    @classmethod
    def _get_command_name(cls, cmd: Command) -> Optional[str]:
        """获取命令名称
        
        Args:
            cmd: 原始命令
            
        Returns:
            Optional[str]: 命令名称
        """
        if cmd.type == CommandType.DIALOGUE:
            return cmd.character
        elif cmd.type == CommandType.BG or cmd.type == CommandType.BGM:
            return cmd.name
        return None

    @classmethod
    def _get_command_content(cls, cmd: Command) -> Optional[str]:
        """获取命令内容
        
        Args:
            cmd: 原始命令
            
        Returns:
            Optional[str]: 命令内容
        """
        if cmd.type == CommandType.JUMP:
            return cmd.target
        return cmd.text if hasattr(cmd, "text") else None

    @classmethod
    def _is_target_protagonist(cls, cmd: Command, protagonist_name: str) -> bool:
        """判断命令目标是否是主角
        
        Args:
            cmd: 原始命令
            protagonist_name: 主角名字
            
        Returns:
            bool: 是否以主角为目标
        """
        return (
            cmd.type == CommandType.DIALOGUE and 
            getattr(cmd, "target", None) == protagonist_name
        )

    @classmethod
    def _get_scene_image_url(cls, cmd: Command, game: "DBGame") -> Optional[str]:
        """获取场景图片URL
        
        Args:
            cmd: 原始命令
            game: 游戏对象
            
        Returns:
            Optional[str]: 场景图片URL
        """
        if not (cmd.type == CommandType.BG and game.scene_image_resources):
            return None
        return next(
            (item.image_url for item in game.scene_image_resources 
             if item.scene_name == cmd.name),
            None
        )

    @classmethod
    def _get_dialogue_audio_url(cls, cmd: Command, game: "DBGame") -> Optional[str]:
        """获取对话音频URL
        
        Args:
            cmd: 原始命令
            game: 游戏对象
            
        Returns:
            Optional[str]: 对话音频URL
        """
        if not (cmd.type == CommandType.DIALOGUE and game.dialogue_tts_resources):
            return None
        return next(
            (item.audio_url for item in game.dialogue_tts_resources 
             if item.character_name == cmd.character),
            None
        )

    @classmethod
    def _get_bgm_url(cls, cmd: Command, game: "DBGame") -> Optional[str]:
        """获取背景音乐URL
        
        Args:
            cmd: 原始命令
            game: 游戏对象
            
        Returns:
            Optional[str]: 背景音乐URL
        """
        if not (cmd.type == CommandType.BGM and game.background_music_resources):
            return None
        return next(
            (item.audio_url for item in game.background_music_resources 
             if item.bgm_name == cmd.name),
            None
        )

    @classmethod
    def _get_command_url(cls, cmd: Command, game: "DBGame") -> Optional[str]:
        """获取命令关联的资源URL
        
        Args:
            cmd: 原始命令
            game: 游戏对象
            
        Returns:
            Optional[str]: 资源URL
        """
        return (
            cls._get_scene_image_url(cmd, game) or
            cls._get_dialogue_audio_url(cmd, game) or
            cls._get_bgm_url(cmd, game)
        )

    @classmethod
    def _convert_command(cls, cmd: Command, game: "DBGame", protagonist_name: str) -> "DBGameCommand":
        """转换单个命令为运行时命令

        Args:
            cmd: 原始命令
            game: 游戏对象，用于获取资源
            protagonist_name: 主角名字，用于判断对话目标

        Returns:
            DBGameCommand: 运行时命令对象
        """
        return DBGameCommand(
            type=cls._get_command_type(cmd),
            name=cls._get_command_name(cmd),
            content=cls._get_command_content(cmd),
            is_target_protagonist=cls._is_target_protagonist(cmd, protagonist_name),
            oss_url=cls._get_command_url(cmd, game)
        )

    @classmethod
    def _process_commands(cls, commands: List[Command], game: "DBGame", protagonist_name: str) -> List[DBGameCommand]:
        """处理命令列表，支持命令合并等逻辑
        
        Args:
            commands: 原始命令列表
            game: 游戏对象，用于获取资源
            protagonist_name: 主角名字，用于判断对话目标
            
        Returns:
            List[DBGameCommand]: 处理后的命令列表
        """
        result = []
        choices = []
        
        for cmd in commands:
            if cmd.type == CommandType.CHOICE:
                choices.append({"text": cmd.text, "target": cmd.target})
            else:
                # 如果之前有选项，先添加选项命令
                if choices:
                    result.append(cls._convert_command(BaseCommand(
                        type=CommandType.CHOICE,
                        text=json.dumps(choices, ensure_ascii=False),
                        name=None
                    ), game, protagonist_name))
                    choices = []
                # 添加当前命令
                result.append(cls._convert_command(cmd, game, protagonist_name))
        
        # 处理最后的选项
        if choices:
            result.append(DBGameCommand(
                type=CommandType.CHOICE,
                content=json.dumps(choices, ensure_ascii=False),
                name=None
            ))
        
        return result

    @classmethod
    def convert_to_runtime_game(cls, game: "DBGame") -> "DBRuntimeGame":
        """转换游戏对象为运行时游戏对象

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
                
            # 获取主角名字
            protagonist_name = next(
                (char.name for char in game.story_character_info.characters if char.is_protagonist),
                None
            )
            
            # 构建分支列表
            runtime_branches = []
            for branch in chapter.branches:
                runtime_branch = DBRuntimeBranch(
                    name=branch.name,
                    commands=cls._process_commands(branch.commands, game, protagonist_name)
                )
                runtime_branches.append(runtime_branch)
            
            # 构建章节
            runtime_chapter = DBRuntimeChapter(
                id=str(chapter.id),
                index=chapter.index,
                title=chapter.title or f"第{chapter.index + 1}章",
                branches=runtime_branches,
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
            tags=game.story_character_info.tags,
            total_chapters=len(runtime_chapters),
            chapters=runtime_chapters,
            metadata={
                "original_game_id": str(game.id),
                "settings": game.settings
            }
        )
        
        return runtime_game
