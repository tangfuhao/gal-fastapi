from pydantic import BaseModel, Field

class AdminUpdateCreditsRequest(BaseModel):
    """管理员更新用户积分的请求"""
    amount: int = Field(description="积分变更数量，正数表示增加，负数表示减少")
    reason: str = Field(description="积分变更原因", min_length=1, max_length=200)
