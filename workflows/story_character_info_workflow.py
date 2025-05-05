from workflows.base_workflow import Workflow, WorkflowResult
from models.game import DBGame, GameGenerationProgress, StoryCharacterInfo
from utils.llm_tool import LLMTool
from repositories.base_repository import BaseRepository
import logging
import json
import re
from utils.voice_style_utils import format_voice_styles
from constant.speaker import speaker_voice_style

logger = logging.getLogger(__name__)

class StoryCharacterInfoWorkflow(Workflow[DBGame]):
    """角色信息提取工作流，处理小说角色信息的提取"""

    def __init__(self, game_repository: BaseRepository[DBGame]):
        self.game_repository = game_repository

    async def execute(self, game: DBGame) -> WorkflowResult[DBGame]:
        """
        从小说内容中提取角色信息并更新数据库
        
        Args:
            game: 游戏数据对象
            
        Returns:
            WorkflowResult[DBGame]: 工作流执行结果，包含更新后的game对象或错误信息
        """
        try:
            # 调用LLMTool的generate方法
            llm_tool = LLMTool()
            completion = await llm_tool.generate(
                system_prompt="story_character_analysis_system",
                user_prompt="story_character_analysis_user",
                prompt_replacements={"content": game.novel_text, "voice_library": format_voice_styles(speaker_voice_style)}
            )

            # 解析角色信息
            try:
                json_match = re.search(r'```json\s*(.*?)\s*```', completion, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = completion

                story_character_info = StoryCharacterInfo.model_validate(
                    json.loads(json_str)
                )
            except (json.JSONDecodeError, ValidationError) as e:
                return WorkflowResult(
                    success=False,
                    error="Failed to parse character info",
                    error_details={"raw_content": completion, "error": str(e)}
                )

            # 更新进度
            generate_progress = GameGenerationProgress(
                current_workflow="story_character_info",
                progress=10
            )

            # 使用数据仓库更新数据库
            update_success = await self.game_repository.update(
                id=game.id,
                fields={
                    "story_character_info": story_character_info,
                    "progress": generate_progress
                }
            )

            if not update_success:
                return WorkflowResult(
                    success=False,
                    error="Failed to update game data"
                )

            # 更新game对象
            game.story_character_info = story_character_info
            game.progress = generate_progress

            return WorkflowResult(
                success=True,
                data=game
            )

        except Exception as e:
            logger.error(f"Character info extraction failed: {str(e)}")
            return WorkflowResult(
                success=False,
                error=f"Character info extraction failed: {str(e)}"
            )
