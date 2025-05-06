from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from bson import ObjectId
from enum import Enum
import asyncio
import logging

from models.game import DBGame, GameStatus, UserInfo, GameGenerationProgress, InputTextType
from models.types import PyObjectId
from models.user import DBUser
from models.db_runtime_game import DBRuntimeGame
from workflows.game_generation import GameGenerationWorkflow
from core.auth import get_current_user
from core.container import get_game_repository, get_runtime_game_repository
from schemas.game_runtime import GameRuntimeSchema
from schemas.game_list import GameListItemSchema
from utils.text import TextUtils
from utils.llm_tool import LLMTool
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class CreateGameRequest(BaseModel):
    """创建游戏请求模型"""
    title: str
    novel_text: str
    settings: dict = {}


class CreateGameStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"

class CreateGameResponse(BaseModel):
    """创建游戏响应模型"""
    task_id: Optional[str]
    status: CreateGameStatus


# 创建路由
games_router = APIRouter(prefix="/api/games", tags=["games"])


@games_router.post("/create", response_model=CreateGameResponse)
async def create_game(
    request: CreateGameRequest,
    current_user: DBUser = Depends(get_current_user),
    game_repo: BaseRepository[DBGame] = Depends(get_game_repository),
    runtime_game_repo: BaseRepository[DBRuntimeGame] = Depends(get_runtime_game_repository)
):
    """创建新游戏"""
    try:
        # 截取一定长度的文本
        text_to_analyze = TextUtils.truncate_by_complete_lines(request.novel_text, 5000)      

        # 先调用大模型检查内容类型
        llm_tool = LLMTool()
        content_type_result = await llm_tool.generate(
            system_prompt="analyze_content_types_system",
            user_prompt="analyze_content_types_user",
            prompt_replacements={"content": text_to_analyze}
        )
        
        # 提取类型并映射到 InputTextType
        type_mapping = {
            "想法": InputTextType.IDEA,
            "小说": InputTextType.NOVEL,
            "无意义": None  # 无意义内容将抛出异常
        }
        
        # 从结果中提取类型
        content_type_match = content_type_result.split("分类结果:")[-1].strip()
        input_type = type_mapping.get(content_type_match)
        
        if input_type is None:
            return CreateGameResponse(
                task_id=None,
                status=CreateGameStatus.FAILED
            )

        # 创建游戏记录
        game = DBGame(
            user_id=current_user.id,
            user_info=UserInfo(
                name=current_user.name,
                avatar_url=current_user.avatar
            ),
            title=request.title,
            input_text_type=input_type,
            input_text=request.novel_text,
            novel_text=text_to_analyze,
            settings=request.settings,
            progress=GameGenerationProgress(current_workflow="", progress=0),
            status=GameStatus.GENERATING,
            generate_chapter_index=1
        )

        # 保存到数据库
        if not await game_repo.create(game):
            raise HTTPException(status_code=500, detail="Failed to create game")
        
        # 启动游戏生成工作流
        workflow = GameGenerationWorkflow(game_repo, runtime_game_repo)
        asyncio.create_task(workflow.generate_game(game))
        
        return CreateGameResponse(
            task_id=str(game.id),
            status=CreateGameStatus.SUCCESS
        )
        
    except Exception as e:
        logger.error(f"Failed to create game: {str(e)}")
        return CreateGameResponse(
            status=CreateGameStatus.FAILED
        )


@games_router.post("/{game_id}/regenerate", response_model=CreateGameResponse)
async def generate_game(
    game_id: str,
    current_user: DBUser = Depends(get_current_user),
    game_repo: BaseRepository[DBGame] = Depends(get_game_repository),
    runtime_game_repo: BaseRepository[DBRuntimeGame] = Depends(get_runtime_game_repository)
):
    try:
        #game_id转成ObjectId
        game_id = PyObjectId(game_id)
        # 查找游戏记录
        game = await game_repo.get(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # 验证游戏状态
        if game.status != GameStatus.FAILED:
            raise HTTPException(status_code=400, detail="Game is not in failed state")

        # 验证用户权限
        if str(game.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=403, detail="Not authorized to regenerate this game"
            )
        
        # 更新状态为生成中
        await game_repo.update(
            id=game.id,
            fields={"status": GameStatus.GENERATING}
        )
        game.status = GameStatus.GENERATING

        # 启动游戏生成工作流
        workflow = GameGenerationWorkflow(game_repo, runtime_game_repo)
        asyncio.create_task(workflow.generate_game(game))

        return CreateGameResponse(
            task_id=str(game.id),
            status=CreateGameStatus.SUCCESS
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to regenerate game: {str(e)}"
        )


@games_router.post("/{game_id}/next_chapter", response_model=CreateGameResponse)
async def generate_next_chapter(
    game_id: str,
    current_user: DBUser = Depends(get_current_user),
    game_repo: BaseRepository[DBGame] = Depends(get_game_repository)
):
    try:
        # 查找游戏记录
        game = await game_repo.get(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # 验证游戏状态
        if game.status != GameStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Game is not in completed state")

        # 验证用户权限
        if str(game.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=403, detail="Not authorized to generate next chapter"
            )

        # 增加 generate_chapter_index
        game.generate_chapter_index += 1
        game.status = GameStatus.GENERATING
        await game_repo.update(
            id=game.id,
            fields={"generate_chapter_index": game.generate_chapter_index, "status": GameStatus.GENERATING}
        )
        
        # 启动游戏生成工作流
        workflow = GameGenerationWorkflow(game_repo)
        asyncio.create_task(workflow.generate_game(game))

        return CreateGameResponse(
            task_id=str(game.id),
            status=CreateGameStatus.SUCCESS
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate next chapter: {str(e)}"
        )


@games_router.get("/{game_id}", response_model=GameRuntimeSchema)
async def get_game(
    game_id: str,
    runtime_game_repo: BaseRepository[DBRuntimeGame] = Depends(get_runtime_game_repository)
):
    try:
        #game_id转成ObjectId
        game_pid = PyObjectId(game_id)

        # 从 runtime_games 获取
        runtime_game = await runtime_game_repo.get(game_pid)
        if not runtime_game:
            raise HTTPException(status_code=404, detail="Game not found")

        # 转换为响应模型
        result = GameRuntimeSchema.from_db_runtime_game(runtime_game)
        return result

    except Exception as e:
        logger.error(f"Failed to get game: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Failed to get game: {str(e)}")


@games_router.get("/", response_model=List[GameListItemSchema])
async def list_games(
    skip: int = 0,
    limit: int = 20,
    tag: Optional[str] = None,
    runtime_game_repo: BaseRepository[DBRuntimeGame] = Depends(get_runtime_game_repository),
):
    try:
        # 构建查询条件
        query = {"is_deleted": False}
        if tag:
            query["tags"] = tag

        # 获取已发布的游戏
        games = await runtime_game_repo.find_many(
            query, 
            skip=skip, 
            limit=limit,
            sort=[("published_at", -1)]  # 按发布时间倒序排序
        )
        return [GameListItemSchema.from_db_runtime_game(game) for game in games]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list games: {str(e)}")
