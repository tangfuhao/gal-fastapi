import json
import asyncio
from datetime import datetime
from pathlib import Path
import sys
import os

# 设置path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.clients import DeepSeekClient
from utils.prompt_manager import PromptManager
from workflows.story_character_info_workflow import StoryCharacterInfoWorkflow
from utils.voice_style_utils import format_voice_styles
from constant.speaker import speaker_voice_style

async def analyze_story_characters(content: str) -> dict:
    """使用 StoryCharacterInfoWorkflow 分析小说人物"""
    client = DeepSeekClient()
    prompt_manager = PromptManager()
    workflow = StoryCharacterInfoWorkflow(client, prompt_manager)
    
    result = await workflow.execute(
        system_prompt="story_character_analysis_system",
        user_prompt="story_character_analysis_user",
        prompt_replacements={"content": content, "voice_library": format_voice_styles(speaker_voice_style)}
    )
    return result

def main():
    # 读取小说内容
    with open("data/小说1.txt", "r", encoding="utf-8") as f:
        content = f.read()

    try:
        # 调用人物分析
        print("正在分析小说人物信息...")
        character_info = asyncio.run(analyze_story_characters(content))

        # 创建输出目录
        output_dir = Path("output/story_characters")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # 生成输出文件名（使用时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_output_path = output_dir / f"character_info_{timestamp}.json"
        
        # 保存人物分析数据（JSON格式）
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(character_info, f, ensure_ascii=False, indent=2)

        # 同时在output根目录保存最新版本
        latest_path = Path("output/story_characters.json")
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(character_info, f, ensure_ascii=False, indent=2)

        print(f"人物分析完成！")
        print(f"JSON格式结果已保存到: {json_output_path}")
        print(f"最新结果同时保存到: {latest_path}")

    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()
