from models.db_runtime_game import DBRuntimeGame
from workflows.base_workflow import Workflow, WorkflowResult
from models.game import DBGame, GameGenerationProgress, GameStatus
from workflows.story_character_info_workflow import StoryCharacterInfoWorkflow
from workflows.chapter_workflows import ChapterSplitWorkflow
from workflows.script_generation_workflow import ScriptGenerationWorkflow
from workflows.script_background_workflow import ScriptBackgroundWorkflow
from workflows.script_bgm_workflow import ScriptBGMWorkflow
from workflows.character_image_workflow import CharacterImageWorkflow
from workflows.scene_image_workflow import SceneImageWorkflow
from workflows.dialogue_tts_workflow import DialogueTTSWorkflow
from workflows.background_music_workflow import BackgroundMusicWorkflow
from repositories.base_repository import BaseRepository
import logging
from typing import Dict, Type

logger = logging.getLogger(__name__)

class GameGenerationWorkflow:
    """游戏生成主工作流，协调所有子工作流的执行"""

    def __init__(self, game_repository: BaseRepository[DBGame], runtime_game_repository: BaseRepository[DBRuntimeGame]):
        self.game_repository = game_repository
        self.runtime_game_repository = runtime_game_repository
        self._workflow_types: Dict[str, Type[Workflow]] = {
            "story_character_info": StoryCharacterInfoWorkflow,
            "chapter_split": ChapterSplitWorkflow,
            "script_generation": ScriptGenerationWorkflow,
            "script_background": ScriptBackgroundWorkflow,
            "script_bgm": ScriptBGMWorkflow,
            "character_image": CharacterImageWorkflow,
            "scene_image": SceneImageWorkflow,
            "dialogue_tts": DialogueTTSWorkflow,
            "background_music": BackgroundMusicWorkflow,
        }

    async def generate_game(self, game: DBGame):
        """从上次失败的地方重新开始游戏生成流程"""
        try:

            # 获取当前工作流索引
            current_workflow = game.progress.current_workflow
            try:
                workflow_index = list(self._workflow_types.keys()).index(current_workflow)
            except ValueError:
                workflow_index = -1

            logger.info(f"当前工作流: {current_workflow}, 索引: {workflow_index}")

            # 从当前工作流开始执行
            workflow_names = list(self._workflow_types.keys())
            for i, workflow_name in enumerate(workflow_names):
                if i <= workflow_index:
                    logger.info(f"跳过已完成的工作流: {workflow_name}")
                    continue

                workflow_type = self._workflow_types[workflow_name]
                workflow = workflow_type(self.game_repository)
                logger.info(f"开始执行工作流: {workflow_name}")
                result = await workflow.execute(game)
                logger.info(f"工作流 {workflow_name} 执行完成")

                if not result.success:
                    # 更新失败状态和错误信息
                    await self.game_repository.update(
                        id=game.id,
                        fields={
                            "status": GameStatus.FAILED,
                            "error": result.error,
                            "error_details": result.error_details
                        }
                    )
                    return

                game = result.data

            # 最后更新所有章节数据并创建运行时游戏
            runtime_game = DBRuntimeGame.convert_to_runtime_game(game)

            # 将运行时游戏保存到数据库
            runtime_game = await self.runtime_game_repository.create(
                runtime_game
            )

            # 更新原始游戏状态
            await self.game_repository.update(
                id=game.id,
                fields={
                    "runtime_id": runtime_game.id,
                    "status": GameStatus.COMPLETED,
                }
            )
            logger.info("游戏重新生成完成")
        except Exception as e:
            logger.error(f"游戏重新生成失败: {str(e)}")
            await self.game_repository.update(
                id=game.id,
                fields={
                    "status": GameStatus.FAILED,
                    "error": str(e)
                }
            )
