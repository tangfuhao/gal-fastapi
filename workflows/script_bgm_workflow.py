from workflows.base_workflow import Workflow, WorkflowResult
from models.game import DBGame, GameGenerationProgress, GameChapter, ChapterGenerationStatus
from utils.llm_tool import LLMTool
from repositories.base_repository import BaseRepository
from utils.script_coder import parse_script, ScriptValidationError, serialize_script
import logging
import json
import re
import asyncio

logger = logging.getLogger(__name__)

class ScriptBGMWorkflow(Workflow[DBGame]):
    """背景音樂生成工作流，處理小說章節的背景音樂生成"""

    def __init__(self, game_repository: BaseRepository[DBGame]):
        self.game_repository = game_repository

    async def execute(self, game: DBGame) -> WorkflowResult[DBGame]:
        """
        為小說章節生成背景音樂並更新資料庫
        
        Args:
            game: 遊戲資料物件
            
        Returns:
            WorkflowResult[DBGame]: 工作流執行結果
        """
        try:
            if not game.chapters:
                return WorkflowResult(
                    success=False,
                    error="No chapters found in game"
                )

            llm_tool = LLMTool()
            is_success = True
            updated_chapters = []

            # 过滤出需要生成背景音乐的章节
            chapters_to_generate = [
                chapter for chapter in game.chapters 
                if chapter.index < game.generate_chapter_index 
                and chapter.generation_status == ChapterGenerationStatus.BACKGROUND_GENERATED
            ]

            if not chapters_to_generate:
                return WorkflowResult(
                    success=True,
                    data=game
                )

            # 并发生成背景音乐
            async def generate_chapter_bgm(chapter: GameChapter) -> tuple[GameChapter, bool]:
                try:
                    # 将branches序列化成脚本内容
                    script_content = serialize_script(chapter.branches)

                    # 生成背景音乐
                    completion = await llm_tool.generate(
                        system_prompt="novel_script_bgm_system",
                        user_prompt="novel_script_bgm_user",
                        prompt_replacements={
                            "script": script_content
                        }
                    )

                    # 解析背景音乐数据
                    branches = parse_script(completion)
                    chapter.branches = branches
                    chapter.generation_status = ChapterGenerationStatus.BGM_GENERATED
                    return chapter, True
                except ScriptValidationError as e:
                    logger.error(f"Failed to parse BGM for chapter {chapter.index}: {str(e)}")
                    return chapter, False
                except Exception as e:
                    logger.error(f"BGM generation failed for chapter {chapter.index}: {str(e)}")
                    return chapter, False

            # 并发执行所有章节的BGM生成
            results = await asyncio.gather(
                *[generate_chapter_bgm(chapter) for chapter in chapters_to_generate]
            )

            # 处理结果
            is_success = True
            chapter_map = {chapter.index: chapter for chapter in game.chapters}  # 保存所有章节的映射
            
            for chapter, success in results:
                if not success:
                    is_success = False
                chapter_map[chapter.index] = chapter  # 更新或添加生成的章节
            
            # 重建章节列表，保持原有顺序
            updated_chapters = [chapter_map[i] for i in range(0, len(chapter_map) )]

            # 更新进度
            generate_progress = GameGenerationProgress(
                current_workflow="script_bgm",
                progress=50
            ) if is_success else game.progress

            # 更新游戏对象
            game.chapters = updated_chapters
            game.progress = generate_progress

            # 使用数据仓库更新数据库
            update_success = await self.game_repository.update(
                id=game.id,
                fields={
                    "chapters": game.chapters,
                    "progress": game.progress
                }
            )

            if not update_success:
                return WorkflowResult(
                    success=False,
                    error="Failed to update game data"
                )

            return WorkflowResult(
                success=is_success,
                data=game,
                error="Some chapters failed to generate BGM" if not is_success else None
            )

        except Exception as e:
            logger.error(f"BGM generation failed: {str(e)}")
            return WorkflowResult(
                success=False,
                error=f"BGM generation failed: {str(e)}"
            )