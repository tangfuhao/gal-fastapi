from motor.motor_asyncio import AsyncIOMotorCollection
from models.credits import DBCredits, DBCreditsHistory
from repositories.mongo_repository import MongoRepository
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CreditsRepository(MongoRepository[DBCredits]):
    """积分数据仓库的具体实现"""

    def __init__(self, collection: AsyncIOMotorCollection, history_collection: AsyncIOMotorCollection):
        super().__init__(collection, DBCredits)
        self.history_collection = history_collection
        

    async def get_by_user_id(self, user_id: str) -> Optional[DBCredits]:
        """获取用户积分"""
        try:
            credits_data = await self.collection.find_one({"user_id": user_id})
            if credits_data:
                return DBCredits.model_validate(credits_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get user credits: {str(e)}")
            return None

    async def deduct_credits(self, user_id: str, amount: int = 1, reason: str = "生成游戏") -> bool:
        """扣除用户积分
        
        Args:
            user_id: 用户ID
            amount: 扣除的数量，默认为1
            reason: 扣除原因
            
        Returns:
            bool: 是否扣除成功
        """
        try:
            # 确保amount是正数
            deduct_amount = abs(amount)
            
            # 原子操作：检查并更新积分
            result = await self.collection.update_one(
                {
                    "user_id": user_id,
                    "amount": {"$gte": deduct_amount}  # 确保有足够的积分
                },
                {
                    "$inc": {"amount": -deduct_amount},
                    "$set": {"updated_at": datetime.now()}
                }
            )

            if result.modified_count > 0:
                # 记录历史
                history = DBCreditsHistory(
                    user_id=user_id,
                    amount=-deduct_amount,
                    reason=reason
                )
                await self.history_collection.insert_one(history.model_dump(by_alias=True))
                return True
                
            return False
        except Exception as e:
            logger.error(f"Failed to deduct user credits: {str(e)}")
            return False

    async def add_credits(self, user_id: str, amount: int, reason: str) -> bool:
        """增加用户积分"""
        try:
            # 确保amount是正数
            add_amount = abs(amount)
            
            # 更新或创建积分记录
            result = await self.collection.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"amount": add_amount},
                    "$set": {"updated_at": datetime.now()},
                    "$setOnInsert": {
                        "created_at": datetime.now()
                    }
                },
                upsert=True
            )

            if result.modified_count > 0 or result.upserted_id:
                # 记录历史
                history = DBCreditsHistory(
                    user_id=user_id,
                    amount=add_amount,
                    reason=reason
                )
                await self.history_collection.insert_one(history.model_dump(by_alias=True))
                return True
                
            return False
        except Exception as e:
            logger.error(f"Failed to add user credits: {str(e)}")
            return False
