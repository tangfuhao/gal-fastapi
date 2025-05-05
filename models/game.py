from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from bson import ObjectId
from models.types import PyObjectId
from schemas.script_commands import Branch

class ResourceType(str, Enum):
    """资源类型枚举"""
    CHARACTER = "character"  # 角色立绘
    BACKGROUND = "background"  # 背景图片
    BGM = "bgm"  # 背景音乐
    VOICE = "voice"  # 语音
    EFFECT = "effect"  # 音效

class ResourceData(BaseModel):
    """资源数据"""
    resource_type: ResourceType = Field(..., description="资源类型")
    chapter_index: int = Field(..., ge=0, description="所属章节索引")
    name: str = Field(..., min_length=1, max_length=100, description="资源名称")
    description: Optional[str] = Field(default=None, max_length=500, description="资源描述")
    url: Optional[str] = Field(default=None, description="资源URL")
    oss_url: Optional[str] = Field(default=None, description="OSS资源URL")
    status: str = Field(default="pending", description="资源状态")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    metadata: Dict = Field(default_factory=dict, description="额外元数据")

class ChapterGenerationStatus(str, Enum):
    """章節生成狀態"""
    NOT_GENERATED = "not_generated"  # 未生成
    SCRIPT_GENERATED = "script_generated"  # 已生成腳本
    BACKGROUND_GENERATED = "background_generated"  # 已生成背景圖
    BGM_GENERATED = "bgm_generated"  # 已生成背景音樂（生成完畢）

class GameChapter(BaseModel):
    """游戏章节模型"""
    id: PyObjectId = Field(default_factory=PyObjectId, description="章节ID")
    index: int = Field(..., ge=0, description="章节序号")
    summary: str = Field(..., max_length=500, description="章节摘要")
    content: str = Field(..., description="章节内容")
    chapter_start_line: int = Field(..., ge=0, description="章节在原文中的起始行")
    chapter_end_line: int = Field(..., ge=0, description="章节在原文中的结束行")
    title: Optional[str] = Field(default=None, max_length=100, description="章节标题")
    branches: List[Branch] = Field(default_factory=list, description="章节脚本分支")
    generation_status: ChapterGenerationStatus = Field(default=ChapterGenerationStatus.NOT_GENERATED, description="章节生成状态")

    @field_validator("chapter_end_line")
    @classmethod
    def validate_chapter_lines(cls, v: int, info) -> int:
        """验证章节结束行大于起始行"""
        if "chapter_start_line" in info.data and v <= info.data["chapter_start_line"]:
            raise ValueError("章节结束行必须大于起始行")
        return v

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        populate_by_name = True

class GameStatus(str, Enum):
    """游戏生成状态枚举"""
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class GameGenerationProgress(BaseModel):
    """游戏生成进度"""
    current_workflow: str = Field(..., description="当前执行的工作流")
    progress: int = Field(default=0, ge=0, le=100, description="当前进度(0-100)")
    completed_workflows: List[str] = Field(default_factory=list, description="已完成的工作流")
    error_message: Optional[str] = Field(default=None, description="错误信息")

class InputTextType(str, Enum):
    """输入文本类型"""
    NOVEL = "novel"
    IDEA = "idea"

class CharacterResource(BaseModel):
    """角色资源数据"""
    character_name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    image_url: str = Field(..., description="角色图片URL")

class DialogueTTSResource(BaseModel):
    """对话TTS资源数据"""
    chapter_index: int = Field(..., ge=0, description="章节索引")
    character_name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    audio_url: str = Field(..., description="音频URL")
    text: str = Field(..., description="对话文本")

class SceneImageResource(BaseModel):
    """场景图资源数据"""
    chapter_index: int = Field(..., ge=0, description="章节索引")
    scene_name: str = Field(..., min_length=1, max_length=100, description="场景名称")
    image_url: str = Field(..., description="图片URL")

class BackgroundMusicResource(BaseModel):
    """背景音乐资源数据"""
    chapter_index: int = Field(..., ge=0, description="章节索引")
    bgm_name: str = Field(..., min_length=1, max_length=100, description="音乐名称")
    prompt: str = Field(..., description="生成提示词")
    audio_url: str = Field(..., description="音频URL")

class UserInfo(BaseModel):
    """用户信息"""
    name: str = Field(..., min_length=1, max_length=50, description="用户名称")
    avatar_url: Optional[str] = Field(default=None, description="用户头像URL")

class Character(BaseModel):
    """Character information model"""
    name: str = Field(..., description="Character name")
    gender: str = Field(..., description="Character gender")
    is_protagonist: bool = Field(..., description="Whether this character is a protagonist")
    description: Dict = Field(default_factory=dict, description="Character description details")
    voice_match: str = Field(..., description="Voice library entry reference")
    image_prompt: str = Field(..., description="Image generation prompt for the character")


class StoryCharacterInfo(BaseModel):
    """Story character information schema"""
    tags: List[str] = Field(..., description="Story tags")
    characters: List[Character] = Field(..., description="List of characters in the story")


class DBGame(BaseModel):
    """游戏数据库模型"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id", description="游戏ID")
    input_text_type: InputTextType = Field(default=InputTextType.NOVEL, description="输入文本类型")
    input_text: str = Field(..., description="输入文本")
    runtime_id: Optional[PyObjectId] = Field(default=None, description="运行时游戏ID")
    user_id: PyObjectId = Field(..., description="用户ID")
    user_info: UserInfo = Field(..., description="用户信息")
    title: str = Field(..., min_length=0, max_length=100, description="游戏标题")
    novel_text: str = Field(..., description="小说文本")
    settings: dict = Field(default_factory=dict, description="游戏生成设置")
    story_character_info: Optional[StoryCharacterInfo] = Field(default=None, description="角色信息")
    chapters: List[GameChapter] = Field(default_factory=list, description="游戏章节")
    total_chapters: Optional[int] = Field(default=None, ge=0, description="总章节数")
    resources: List[ResourceData] = Field(default_factory=list, description="游戏资源")
    character_resources: List[CharacterResource] = Field(default_factory=list, description="角色资源")
    dialogue_tts_resources: List[DialogueTTSResource] = Field(default_factory=list, description="对话TTS资源")
    scene_image_resources: List[SceneImageResource] = Field(default_factory=list, description="场景图资源")
    background_music_resources: List[BackgroundMusicResource] = Field(default_factory=list, description="背景音乐资源")
    status: GameStatus = Field(default=GameStatus.GENERATING, description="生成状态")
    error: Optional[str] = Field(default=None, description="错误信息")
    progress: GameGenerationProgress = Field(
        default_factory=lambda: GameGenerationProgress(
            current_workflow="pending",
            progress=0
        ),
        description="生成进度",
    )
    #记录当前生成的章节位置
    generate_chapter_index: int = Field(default=0, ge=0, description="当前生成章节索引")
    is_deleted: bool = Field(default=False, description="是否已删除")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    deleted_at: Optional[datetime] = Field(default=None, description="删除时间")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
        populate_by_name = True
