from fastapi import Depends, HTTPException, Request, status
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from core.container import get_container
from models.user import DBUser

async def get_current_user(
    request: Request,
    collection: AsyncIOMotorCollection = Depends(lambda: get_container().users_collection())
) -> DBUser:
    """获取当前登录用户
    
    从cookie中获取user_id,然后从数据库查询用户信息
    如果未登录或用户不存在则抛出401异常
    """
    try:
        # 从cookie获取用户ID
        user_id = request.cookies.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        # 查询用户
        user_dict = await collection.find_one({"_id": ObjectId(user_id)})
        if not user_dict:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
            
        return DBUser(**user_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
