from datetime import datetime
from pydantic import BaseModel, Field

class CreditsResponse(BaseModel):
    credits: int
    updated_at: datetime

class UpdateCreditsRequest(BaseModel):
    amount: int = Field(description="积分变更数量，正数表示增加，负数表示减少")
    reason: str = Field(description="积分变更原因", min_length=1, max_length=200)

class CreditsHistoryResponse(BaseModel):
    amount: int
    reason: str
    created_at: datetime
