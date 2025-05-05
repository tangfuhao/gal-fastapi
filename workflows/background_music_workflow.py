from typing import Any, Dict, Optional
import uuid
import httpx
from schemas.script_commands import BGMCommand, CommandType
from workflows.base_workflow import Workflow, WorkflowResult
from models.game import DBGame, BackgroundMusicResource, GameChapter, GameGenerationProgress, ChapterGenerationStatus
from utils.music_generator import MusicGenerator, MusicTaskStatus
from utils.ali_upload import upload_from_url
from repositories.base_repository import BaseRepository
import logging
import asyncio
from config import get_settings

logger = logging.getLogger(__name__)

class BackgroundMusicWorkflow(Workflow[DBGame]):
    """背景音乐生成工作流，处理游戏场景的背景音乐生成"""

    def __init__(self, game_repository: BaseRepository[DBGame]):
        self.game_repository = game_repository

    async def execute(self, game: DBGame) -> WorkflowResult[DBGame]:
        """
        为游戏场景生成背景音乐并更新数据库
        
        Args:
            game: 游戏数据对象
            
        Returns:
            WorkflowResult[DBGame]: 工作流执行结果，包含更新后的game对象或错误信息
        """
        try:
            if not game.chapters:
                return WorkflowResult(
                    success=False,
                    error="No chapters found in game"
                )

            # 过滤出需要生成背景音乐的章节
            chapters_to_generate = [
                chapter for chapter in game.chapters
                if chapter.generation_status == ChapterGenerationStatus.BGM_GENERATED
                and chapter.index < game.generate_chapter_index
            ]

            if not chapters_to_generate:
                return WorkflowResult(
                    success=False,
                    error="No chapters need to generate background music"
                )
            
            self.music_generator: MusicGenerator = await MusicGenerator.get_instance()

            async def generate_background_music(chapter: GameChapter, bgm_command: BGMCommand):
                try:
                    # 生成背景音乐
                    result = await self.music_generator.generate_music(
                        prompt=bgm_command.prompt
                    )

                    if result and result.status == MusicTaskStatus.SUCCESS and result.oss_audio_url:
                        return {
                            "data": BackgroundMusicResource(
                                chapter_index=chapter.index,
                                bgm_name=bgm_command.name,
                                audio_url=result.oss_audio_url,
                                prompt=bgm_command.prompt,
                            ),
                            "success": True
                        }
                    
                    return {
                        "success": False,
                        "error": "Failed to generate background music"
                    }
                except Exception as e:
                    logger.error(f"Failed to generate background music for chapter {chapter.index}: {str(e)}")
                    return {
                        "success": False,
                        "error": str(e)
                    }

            # 并发生成所有背景音乐
            tasks = []
            for chapter in chapters_to_generate:
                if not chapter.branches:
                    continue
                    
                for branch in chapter.branches:
                    for command in branch.commands:
                        if command.type == CommandType.BGM:
                            bgm_command: BGMCommand = command
                            # 检查是否已经在 background_music_resources 中
                            if any(
                                resource.chapter_index == chapter.index
                                and resource.bgm_name == bgm_command.name
                                for resource in game.background_music_resources
                            ):
                                continue
                            
                            tasks.append(generate_background_music(chapter, bgm_command))

            successful_resources = []
            failed_resources = []
            
            if tasks:
                results = await asyncio.gather(*tasks)
                
                for result in results:
                    if result["success"]:
                        successful_resources.append(result["data"])
                    else:
                        failed_resources.append(result)
                        logger.error(f"Failed to generate background music for chapter {result['chapter_index']}: {result.get('error', 'Unknown error')}")
                
                # 更新 background_music_resources
                if successful_resources:
                    game.background_music_resources.extend(successful_resources)
                
                # 如果有失败的资源，记录日志
                if failed_resources:
                    logger.warning(f"Failed to generate {len(failed_resources)} background music")
                    for failed in failed_resources:
                        logger.warning(f"Chapter {failed['chapter_index']}: {failed.get('error', 'Unknown error')}")

            # 更新进度
            generate_progress = GameGenerationProgress(
                current_workflow="background_music" if not failed_resources else game.progress.current_workflow,
                progress=80 if not failed_resources else game.progress.progress
            )

            # 更新游戏对象
            game.progress = generate_progress

            # 使用数据仓库更新数据库
            update_success = await self.game_repository.update(
                id=game.id,
                fields={
                    "background_music_resources": game.background_music_resources,
                    "progress": generate_progress
                }
            )

            if not update_success:
                return WorkflowResult(
                    success=False,
                    error="Failed to update game data"
                )

            return WorkflowResult(
                success=True if not failed_resources else False,
                data=game,
                error="Some background music failed to generate" if failed_resources else None
            )

        except Exception as e:
            logger.error(f"Background music generation failed: {str(e)}")
            return WorkflowResult(
                success=False,
                error=f"Background music generation failed: {str(e)}"
            )
