from typing import Any, Dict, Optional
import uuid

import httpx
from workflows.base_workflow import Workflow, WorkflowResult
from models.game import Character, DBGame, DialogueTTSResource, GameChapter, GameGenerationProgress, ChapterGenerationStatus, StoryCharacterInfo
from utils.voice_generator import VoiceGenerator
from utils.ali_upload import upload_from_url
from repositories.base_repository import BaseRepository
from schemas.script_commands import CommandType, DialogueCommand
import logging
import asyncio
from config import get_settings

logger = logging.getLogger(__name__)

TTS_API_URL = "https://gsv.ai-lab.top/infer_single"

class DialogueTTSWorkflow(Workflow[DBGame]):
    """对话TTS生成工作流，处理游戏对话的语音生成"""

    def __init__(self, game_repository: BaseRepository[DBGame]):
        self.game_repository = game_repository

    def _find_character(self, character_name: str, story_character_info: StoryCharacterInfo) -> Optional[Character]:
        """
        在角色列表中查找指定名称的角色
        
        Args:
            character_name: 角色名称
            story_character_info: 故事角色信息
            
        Returns:
            Optional[Character]: 找到的角色对象，如果未找到则返回None
        """
        character_info = None
        speaker = character_name.strip()
        
        for char in story_character_info.characters:
            char_name = char.name.strip()
            if not char_name:
                continue
                
            # 1. 完全匹配
            if char_name == speaker:
                character_info = char
                break
            # 2. speaker 包含于 char_name
            elif speaker in char_name:
                character_info = char
                break
            # 3. char_name 包含于 speaker
            elif char_name in speaker:
                character_info = char
                break

        return character_info

    async def call_tts_api(
        self,
        access_token: Optional[str] = None,
        model_name: str = "鸣潮",
        speaker_name: str = None,
        prompt_text_lang: str = "中文",
        emotion: str = "随机",
        text: str = None,
        text_lang: str = "中文",
        top_k: int = 10,
        top_p: int = 1,
        temperature: float = 1.0,
        text_split_method: str = "按标点符号切",
        batch_size: int = 10,
        batch_threshold: float = 0.75,
        split_bucket: bool = True,
        speed_facter: float = 1.0,
        fragment_interval: float = 0.3,
        media_type: str = "aac",
        parallel_infer: bool = True,
        repetition_penalty: float = 1.35,
        seed: int = -1,
        extra_headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        
        # 自动注入 access_token
        if not access_token:
            settings = get_settings()
            access_token = getattr(settings, "TTS_ACCESS_TOKEN", None)
        if not access_token:
            raise ValueError("TTS access_token 未提供且未在配置中设置 TTS_ACCESS_TOKEN")
        payload = {
            "access_token": access_token,
            "model_name": model_name,
            "speaker_name": speaker_name,
            "prompt_text_lang": prompt_text_lang,
            "emotion": emotion,
            "text": text,
            "text_lang": text_lang,
            "top_k": top_k,
            "top_p": top_p,
            "temperature": temperature,
            "text_split_method": text_split_method,
            "batch_size": batch_size,
            "batch_threshold": batch_threshold,
            "split_bucket": split_bucket,
            "speed_facter": speed_facter,
            "fragment_interval": fragment_interval,
            "media_type": media_type,
            "parallel_infer": parallel_infer,
            "repetition_penalty": repetition_penalty,
            "seed": seed,
        }
        payload.update(kwargs)
        headers = {
            "content-type": "application/json",
            "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
            "priority": "u=1, i",
            "authority": "gsv.ai-lab.top",
        }
        if extra_headers:
            headers.update(extra_headers)
        async with httpx.AsyncClient() as client:
            resp = await client.post(TTS_API_URL, json=payload, headers=headers, timeout=60.0)
            resp.raise_for_status()
            result = resp.json()
            
            # 上传音频文件到OSS
            if result and "audio_url" in result:
                # 生成唯一的文件名
                file_ext = result["audio_url"].split(".")[-1]
                unique_filename = f"{uuid.uuid4()}.{file_ext}"
                oss_path = f"gal-test/tts/{unique_filename}"
                
                # 上传到OSS
                upload_success = await upload_from_url(
                    url=result["audio_url"],
                    type="audio",
                    oss_object_path=oss_path
                )
                
                if upload_success:
                    # 替换URL为OSS地址
                    settings = get_settings()
                    oss_url = f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT.replace('https://', '')}/{oss_path}"
                    result["audio_url"] = oss_url
                
            return result

    async def execute(self, game: DBGame) -> WorkflowResult[DBGame]:
        """
        为游戏对话生成语音并更新数据库
        
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

            # 过滤出需要生成语音的章节
            chapters_to_generate = [
                chapter for chapter in game.chapters
                if chapter.generation_status == ChapterGenerationStatus.BGM_GENERATED
                and chapter.index < game.generate_chapter_index
            ]

            if not chapters_to_generate:
                return WorkflowResult(
                    success=False,
                    error="No chapters need to generate dialogue TTS"
                )

            async def generate_dialogue_tts(chapter: GameChapter, dialogue_command: DialogueCommand, character: Character):
                try:
                    if character.voice_match:
                        # 处理可能带有匹配度的情况，如 "巴多里奥（匹配度90%）"
                        speaker_name = character.voice_match.split("（")[0].strip()

                    #打印信息
                    logger.info(f"开始为章节生成tts {chapter.index}, character {dialogue_command.character}, speaker_name {speaker_name}, text {dialogue_command.text}")
                    # 使用语音生成器生成语音
                    result = await self.call_tts_api(
                        text=dialogue_command.text,
                        speaker_name=speaker_name,
                    )
                    logger.info(f"生成tts {dialogue_command.text} ,结果 {result}")

                    if result and result.get("audio_url"):
                        return {
                            "data": DialogueTTSResource(
                                chapter_index=chapter.index,
                                character_name=dialogue_command.character,
                                audio_url=result["audio_url"],  
                                text=dialogue_command.text,
                            ),
                            "success": True
                        }
                    
                    return {
                        "success": False,
                        "error": "Failed to generate or upload voice"
                    }
                except Exception as e:
                    logger.error(f"Failed to generate dialogue TTS for chapter {chapter.index}: {str(e)}")
                    return {
                        "success": False,
                        "error": str(e)
                    }

            # 并发生成所有对话语音
            tasks = []
            for chapter in chapters_to_generate:
                if not chapter.branches:
                    continue
                    
                for branch in chapter.branches:
                    for command in branch.commands:
                        if command.type == CommandType.DIALOGUE:
                            # 查找角色信息
                            character = self._find_character(command.character, game.story_character_info)
                            # 如果不是主角才生成语音
                            if character and not character.is_protagonist:
                                dialogue_command: DialogueCommand = command
                                # 检查是否已经在 dialogue_tts_resources 中
                                if any(
                                    resource.chapter_index == chapter.index and
                                    resource.text == dialogue_command.text
                                    for resource in game.dialogue_tts_resources
                                ):
                                    continue
                                    
                                tasks.append(generate_dialogue_tts(chapter, dialogue_command, character))

            successful_resources = []
            failed_resources = []
            
            if tasks:
                results = await asyncio.gather(*tasks)
                
                for result in results:
                    if result["success"]:
                        successful_resources.append(result["data"])
                    else:
                        failed_resources.append(result)
                        logger.error(f"Failed to generate dialogue TTS for chapter {result['chapter_index']}: {result.get('error', 'Unknown error')}")
                
                # 更新 dialogue_tts_resources
                if successful_resources:
                    game.dialogue_tts_resources.extend(successful_resources)
                
                # 如果有失败的资源，记录日志
                if failed_resources:
                    logger.warning(f"Failed to generate {len(failed_resources)} dialogue TTS")
                    for failed in failed_resources:
                        logger.warning(f"Chapter {failed['chapter_index']}: {failed.get('error', 'Unknown error')}")

            # 更新进度
            generate_progress = GameGenerationProgress(
                current_workflow="dialogue_tts" if not failed_resources else game.progress.current_workflow,
                progress=80 if not failed_resources else game.progress.progress
            )

            # 更新游戏对象
            game.progress = generate_progress

            # 使用数据仓库更新数据库
            update_success = await self.game_repository.update(
                id=game.id,
                fields={
                    "dialogue_tts_resources": game.dialogue_tts_resources,
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
                error="Some dialogue TTS failed to generate" if failed_resources else None
            )

        except Exception as e:
            logger.error(f"Dialogue TTS generation failed: {str(e)}")
            return WorkflowResult(
                success=False,
                error=f"Dialogue TTS generation failed: {str(e)}"
            )
