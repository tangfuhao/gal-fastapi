from .base import ContentRequest, BaseRequest
from pydantic import Field

class NovelChapterScriptRequest(ContentRequest):
    """小说章节剧本转换请求"""
    script_format: str = Field(
        default="standard",
        description="剧本格式：standard-标准格式，detailed-详细格式"
    )

class NovelChapterScriptMediaRequest(BaseRequest):
    """小说章节剧本媒体生成请求"""
    content: str = Field(..., min_length=1, description="原始小说内容")
    script: str = Field(..., min_length=1, description="生成的剧本内容")
    media_type: str = Field(
        default="image",
        description="要生成的媒体类型：image-图片，video-视频，audio-音频"
    )

class ScriptBackgroundRequest(BaseRequest):
    """脚本背景图生成请求"""
    script: str = Field(..., min_length=1, description="生成的剧本内容")
    