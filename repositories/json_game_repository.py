from typing import Any, Coroutine
from models.db_runtime_game import DBRuntimeGame
from models.types import PyObjectId
from repositories.json_repository import JsonRepository
from models.game import DBGame

class JsonGameRepository(JsonRepository[DBGame]):
    """基于JSON文件的游戏数据仓库实现"""
    
    def __init__(self, file_path: str):
        super().__init__(file_path, DBGame)


class JsonRuntimeGameRepository(JsonRepository[DBRuntimeGame]):
    """基于JSON文件的游戏数据仓库实现"""
    
    def __init__(self, file_path: str):
        super().__init__(file_path, DBGame)

    def create(self, model: DBRuntimeGame) -> Coroutine[Any, Any, bool]:
        if not model.id:
            model.id = PyObjectId()
        return super().create(model)