from .base import ContentRequest, BaseRequest
from pydantic import Field
from typing import Optional

class NovelOptimizationRequest(ContentRequest):
    """小说优化请求"""
    optimization_type: str = Field(
        default="general",
        description="优化类型：general-一般优化，style-风格优化，plot-情节优化"
    )

class NovelChapterSplitRequest(ContentRequest):
    """小说章节分割请求"""
    min_chapter_length: int = Field(
        default=1000,
        ge=100,
        description="最小章节长度"
    )

class NovelChapterOptimizationRequest(ContentRequest):
    """小说章节优化请求"""
    chapter_title: Optional[str] = Field(
        default=None,
        description="章节标题，如果不提供则自动生成"
    )
