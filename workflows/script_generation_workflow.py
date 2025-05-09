from workflows.base_workflow import Workflow, WorkflowResult
from models.game import DBGame, GameGenerationProgress, GameChapter, ChapterGenerationStatus
from utils.llm_tool import LLMTool
from repositories.base_repository import BaseRepository
import logging
import json
import re
from typing import Any
import asyncio
from pydantic import ValidationError
from utils.script_coder import parse_script, ScriptValidationError

logger = logging.getLogger(__name__)

class ScriptGenerationWorkflow(Workflow[DBGame]):
    """腳本生成工作流，處理小說章節的腳本生成"""

    def __init__(self, game_repository: BaseRepository[DBGame]):
        self.game_repository = game_repository

    async def execute(self, game: DBGame) -> WorkflowResult[DBGame]:
        """
        為所有章節生成腳本
        
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

            if not game.story_character_info:
                return WorkflowResult(
                    success=False,
                    error="No character information found"
                )
            
            if not game.story_character_info.characters:
                return WorkflowResult(
                    success=False,
                    error="No characters found in character information"
                )

            # 获取角色名列表
            role_names = ", ".join([
                character.name
                for character in game.story_character_info.characters
            ])

            llm_tool = LLMTool()

            # 过滤出需要生成脚本的章节
            chapters_to_generate = [
                chapter for chapter in game.chapters 
                if chapter.index < game.generate_chapter_index 
                and chapter.generation_status == ChapterGenerationStatus.NOT_GENERATED
            ]

            if not chapters_to_generate:
                return WorkflowResult(
                    success=True,
                    data=game
                )

            # 并发生成脚本
            async def generate_chapter_script(chapter: GameChapter) -> tuple[GameChapter, bool]:
                try:
                    # 生成脚本
                    completion = await llm_tool.generate(
                        system_prompt="novel_chapter_script_system",
                        user_prompt="novel_chapter_script_user",
                        prompt_replacements={
                            "content": chapter.content,
                            "role_names": role_names
                        }
                    )

                    branches = parse_script(completion)
                    # 更新章节脚本和状态
                    chapter.branches = branches
                    chapter.generation_status = ChapterGenerationStatus.SCRIPT_GENERATED
                    return chapter, True
                except ScriptValidationError as e:
                    logger.error(f"Failed to parse script for chapter {chapter.index}: {str(e)}")
                    return chapter, False
                except Exception as e:
                    logger.error(f"Script generation failed for chapter {chapter.index}: {str(e)}")
                    return chapter, False

            # 并发执行所有章节的生成
            results = await asyncio.gather(
                *[generate_chapter_script(chapter) for chapter in chapters_to_generate]
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
                current_workflow="script_generation",
                progress=30
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
                error="Some chapters failed to generate script" if not is_success else None
            )

        except Exception as e:
            logger.error(f"Script generation failed: {str(e)}")
            return WorkflowResult(
                success=False,
                error=f"Script generation failed: {str(e)}"
            )