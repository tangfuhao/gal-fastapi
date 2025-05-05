from pydantic import BaseModel, Field, validator
from typing import Optional

class BaseRequest(BaseModel):
    """Base request model with common fields."""
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="控制生成内容的随机性，值越高结果越多样，值越低结果越确定"
    )

    class Config:
        validate_assignment = True

class ContentRequest(BaseRequest):
    """包含内容字段的基础请求模型"""
    content: str = Field(..., min_length=1, description="需要处理的文本内容")

    @validator('content')
    def validate_content_not_empty(cls, v):
        if not v.strip():
            raise ValueError("内容不能为空")
        return v.strip()

