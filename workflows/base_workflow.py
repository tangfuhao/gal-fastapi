from typing import Any, TypeVar, Generic, Protocol, runtime_checkable, Optional
import logging
from pydantic import BaseModel

T = TypeVar('T')  # 定义一个类型变量

logger = logging.getLogger(__name__)

class WorkflowResult(BaseModel, Generic[T]):
    """工作流执行结果"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_details: Optional[dict] = None

@runtime_checkable
class Workflow(Protocol[T]):
    """
    基础工作流协议，定义工作流必须实现的接口。
    使用 Protocol 而不是普通基类，这样子类可以更自由地定义自己的参数。
    """
    async def execute(self, /, *args: Any, **kwargs: Any) -> WorkflowResult[T]: 
        """
        执行工作流
        
        Args:
            /: 位置参数标记，之后的参数可以是位置参数或关键字参数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            WorkflowResult[T]: 工作流执行结果，包含成功/失败状态和数据/错误信息
        """
        ...
