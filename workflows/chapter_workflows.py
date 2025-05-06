import json
import re
from typing import List, Dict, Any, Optional
import logging
from models.game import GameChapter, DBGame, GameGenerationProgress
from models.types import PyObjectId
from workflows.base_workflow import Workflow, WorkflowResult
from utils.llm_tool import LLMTool
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

async def parse_chapters(game: DBGame, chapters_data: List[Dict[str, Any]]) -> List[GameChapter]:
    """解析章节数据
    
    Args:
        game: 游戏对象
        chapters_data: 章节数据列表
        
    Returns:
        章节对象列表
    """
    try:
        # 为每个章节添加必填字段
        chapters = []
        for i, chapter_data in enumerate(chapters_data):
            # 获取章节内容
            start_line = chapter_data['chapter_start_line']
            end_line = chapter_data['chapter_end_line']
            content = '\n'.join(game.novel_text.splitlines()[start_line-1:end_line])
            
            # 补充必填字段
            chapter_data['id'] = PyObjectId()  # 添加 id 字段
            chapter_data['index'] = i
            chapter_data['content'] = content
            chapter_data['branches'] = []
            
            # 创建章节对象
            chapter = GameChapter.model_validate(chapter_data)
            chapters.append(chapter)
            
        return chapters
    except Exception as e:
        logger.error(f"解析章节数据失败: {str(e)}")
        raise

class ChapterSplitWorkflow(Workflow[DBGame]):
    """章节分割工作流"""

    def __init__(self, game_repository: BaseRepository[DBGame]):
        self.game_repository = game_repository

    async def execute(self, game: DBGame) -> WorkflowResult[DBGame]:
        """执行章节分割工作流
        
        Args:
            game: 游戏对象
            
        Returns:
            执行结果
        """
        try:
            # 调用LLMTool的generate方法
            llm_tool = LLMTool()
            completion = await llm_tool.generate(
                system_prompt="novel_chapter_split_system",
                user_prompt="novel_chapter_split_user",
                prompt_replacements={"content": game.novel_text}
            )

            # 解析返回的章节数据
            try:
                json_match = re.search(r'```json\s*(.*?)\s*```', completion, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = completion

                split_chapters_data = json.loads(json_str)
                chapters_data = split_chapters_data["chapters"]
                
                # 解析章节数据
                chapters = await parse_chapters(game, chapters_data)

            except (json.JSONDecodeError, AttributeError) as e:
                return WorkflowResult(
                    success=False,
                    error="Failed to parse chapters data",
                    error_details={"raw_content": completion, "error": str(e)}
                )

            # 更新进度
            generate_progress = GameGenerationProgress(
                current_workflow="chapter_split",
                progress=10
            )

            # 更新游戏对象
            game.chapters = chapters
            game.total_chapters = len(chapters)
            game.progress = generate_progress

            # 使用数据仓库更新数据库
            update_success = await self.game_repository.update(
                id=game.id,
                fields={
                    "chapters": game.chapters,
                    "total_chapters": game.total_chapters,
                    "progress": game.progress 
                }
            )

            if not update_success:
                return WorkflowResult(
                    success=False,
                    error="Failed to update game data"
                )

            return WorkflowResult(
                success=True,
                data=game
            )

        except Exception as e:
            logger.error(f"Chapter split failed: {str(e)}")
            return WorkflowResult(
                success=False,
                error=f"Chapter split failed: {str(e)}"
            )
