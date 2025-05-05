from schemas.script_commands import BackgroundCommand, CommandType
from workflows.base_workflow import Workflow, WorkflowResult
from models.game import DBGame, GameChapter, GameGenerationProgress, ChapterGenerationStatus, SceneImageResource
from utils.image_tool import ImageText2ImageTool
from repositories.base_repository import BaseRepository
import logging
import json
import re
import asyncio

logger = logging.getLogger(__name__)

class SceneImageWorkflow(Workflow[DBGame]):
    """场景图片生成工作流，处理游戏场景的图片生成"""

    def __init__(self, game_repository: BaseRepository[DBGame]):
        self.game_repository = game_repository
        self.image_tool = ImageText2ImageTool()

    async def execute(self, game: DBGame) -> WorkflowResult[DBGame]:
        """
        为游戏场景生成图片并更新数据库
        
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

            # 过滤出需要生成场景图的章节
            chapters_to_generate = [
                chapter for chapter in game.chapters
                if chapter.generation_status == ChapterGenerationStatus.BGM_GENERATED
                and chapter.index < game.generate_chapter_index
            ]

            if not chapters_to_generate:
                return WorkflowResult(
                    success=False,
                    error="No chapters need to generate scene images"
                )

            async def generate_scene_image(chapter: GameChapter, background_command: BackgroundCommand):
                try:
                    # 使用背景命令的 prompt 直接生成图片 宽高比 16:9
                    result = await self.image_tool.async_text2img(
                        prompt=background_command.prompt,
                        width=1024,
                        height=576,
                        upload_to_oss=True,
                        oss_type="scene"
                    )
                    
                    if result.get("oss_url"):
                        return {
                            "data": SceneImageResource(
                                chapter_index=chapter.index,
                                scene_name=background_command.name,
                                image_url=result["oss_url"],
                            ),
                            "success": True
                        }
                    return {
                        "success": False,
                        "error": "No image URL returned"
                    }
                except Exception as e:
                    logger.error(f"Failed to generate scene image for chapter {chapter.index}: {str(e)}")
                    return {
                        "success": False,
                        "error": str(e)
                    }

            # 并发生成所有场景图
            tasks = []
            for chapter in chapters_to_generate:
                if not chapter.branches:
                    continue
                    
                for branch in chapter.branches:
                    for command in branch.commands:
                        if command.type == CommandType.BG:
                            background_command: BackgroundCommand = command
                            # 检查是否已经在 scene_image_resources 中
                            if any(
                                resource.chapter_index == chapter.index and
                                resource.scene_name == background_command.name
                                for resource in game.scene_image_resources
                            ):
                                continue
                                
                            tasks.append(generate_scene_image(chapter, background_command))

            successful_resources = []
            failed_resources = []
            if tasks:
                results = await asyncio.gather(*tasks)
                for result in results:
                    if result["success"]:
                        successful_resources.append(result["data"])
                    else:
                        failed_resources.append(result)
                        logger.error(f"Failed to generate scene image for chapter {result['chapter_index']}: {result.get('error', 'Unknown error')}")
                
                # 更新 scene_image_resources
                if successful_resources:
                    game.scene_image_resources.extend(successful_resources)
                
                # 如果有失败的资源，记录日志
                if failed_resources:
                    logger.warning(f"Failed to generate {len(failed_resources)} scene images")
                    for failed in failed_resources:
                        logger.warning(f"Chapter {failed['chapter_index']}: {failed.get('error', 'Unknown error')}")

            # 更新进度
            generate_progress = GameGenerationProgress(
                current_workflow="scene_image" if not failed_resources else game.progress.current_workflow,
                progress=70 if not failed_resources else game.progress.progress
            )

            # 更新游戏对象
            game.progress = generate_progress

            # 使用数据仓库更新数据库
            update_success = await self.game_repository.update(
                id=game.id,
                fields={
                    "scene_image_resources": game.scene_image_resources,
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
                error="Some scene images failed to generate" if failed_resources else None
            )

        except Exception as e:
            logger.error(f"Scene image generation failed: {str(e)}")
            return WorkflowResult(
                success=False,
                error=f"Scene image generation failed: {str(e)}"
            )
