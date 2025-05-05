from workflows.base_workflow import Workflow, WorkflowResult
from models.game import DBGame, GameGenerationProgress, CharacterResource
from utils.llm_tool import LLMTool
from utils.image_tool import ImageText2ImageTool
from repositories.base_repository import BaseRepository
import logging
import json
import re
from typing import List, Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class CharacterImageWorkflow(Workflow[DBGame]):
    """角色圖片生成工作流，處理角色立繪的生成"""

    def __init__(self, game_repository: BaseRepository[DBGame]):
        self.game_repository = game_repository

    async def execute(self, game: DBGame) -> WorkflowResult[DBGame]:
        """
        為角色生成立繪並更新資料庫
        
        Args:
            game: 遊戲資料物件
            
        Returns:
            WorkflowResult[DBGame]: 工作流執行結果
        """
        try:
            # 檢查角色信息是否存在
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

            # 過濾出需要生成圖片的角色
            characters_to_generate = []
            existing_character_map = {
                resource.character_name: resource.image_url 
                for resource in game.character_resources
            }
            
            new_resources = []
            for character in game.story_character_info.characters:
                if character.name not in existing_character_map:
                    characters_to_generate.append(character)
                else:
                    # 如果角色已存在，創建對應的資源記錄
                    resource = CharacterResource(
                        character_name=character.name,
                        image_url=existing_character_map[character.name]
                    )
                    new_resources.append(resource)

            # 只為新角色生成圖像
            if characters_to_generate:
                # 建立圖片生成任務
                image_tasks = []
                image_tool = ImageText2ImageTool()
                
                for character in characters_to_generate:
                    # 創建圖片生成任務
                    task = image_tool.async_text2img(
                        prompt=character.image_prompt,
                        negative_prompt="bad quality, blurry, distorted, deformed",
                        width=512,
                        height=768,
                        upload_to_oss=True,
                        oss_type="character"
                    )
                    image_tasks.append((character, task))
                
                # 並行執行所有圖片生成任務並等待完成
                results = await asyncio.gather(
                    *[task for _, task in image_tasks],
                    return_exceptions=True
                )
                
                # 處理生成結果
                is_success = True
                for (character, _), result in zip(image_tasks, results):
                    if isinstance(result, Exception):
                        is_success = False
                        logger.error(f"圖片生成失敗，角色 {character.name}: {str(result)}")
                    elif result and "oss_url" in result:
                        # 創建角色資源記錄
                        resource = CharacterResource(
                            character_name=character.name,
                            image_url=result["oss_url"]
                        )
                        new_resources.append(resource)
                    else:
                        is_success = False
                        logger.error(f"圖片生成失敗，角色 {character.name}")
                
                # 更新進度
                generate_progress = GameGenerationProgress(
                    current_workflow="character_image",
                    progress=60
                )
                
                # 更新游戏对象
                game.character_resources = new_resources
                game.progress = generate_progress

                # 使用数据仓库更新数据库
                update_success = await self.game_repository.update(
                    id=game.id,
                    fields={
                        "character_resources": new_resources,
                        "progress": generate_progress
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
                    error="Some character images failed to generate" if not is_success else None
                )
            else:
                # 如果没有需要生成的角色，直接返回成功
                return WorkflowResult(
                    success=True,
                    data=game
                )

        except Exception as e:
            logger.error(f"Character image generation failed: {str(e)}")
            return WorkflowResult(
                success=False,
                error=f"Character image generation failed: {str(e)}"
            )
