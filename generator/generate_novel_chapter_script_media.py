import json
import asyncio
from datetime import datetime
from pathlib import Path
import sys
import os

#设置path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from core.dependencies import get_deepseek_client, get_prompt_manager
from workflows.media_workflows import MediaGenerationWorkflow

async def generate_novel_chapter_script_media(content: str, script: str, temperature: float = 0.7) -> dict:
    """使用 MediaGenerationWorkflow 直接生成媒体内容"""
    client = get_deepseek_client()
    prompt_manager = get_prompt_manager()
    workflow = MediaGenerationWorkflow(client, prompt_manager)
    
    result = await workflow.execute(
        system_prompt="novel_script_media_system",
        user_prompt="novel_script_media_user",
        prompt_replacements={"content": content, "script": script}
    )
    return result

def main():
    # 读取优化后的脚本
    with open("output/optimized_chapters.json", "r", encoding="utf-8") as f:
        optimized_chapters = json.load(f)

    try:
        # 创建输出目录
        output_dir = Path("output/script_media")
        output_dir.mkdir(exist_ok=True)
        
        # 生成输出文件名（使用时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 获取第一个章节的内容
        chapter_content = optimized_chapters['content']
        chapter_script = optimized_chapters['script']

        print("开始生成媒体内容...")
        media_result = asyncio.run(generate_novel_chapter_script_media(
            content=chapter_content,
            script=chapter_script
        ))

        # 保存结果
        output_file = output_dir / f"script_media_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(media_result, f, ensure_ascii=False, indent=2)
            
        # 同时更新到固定路径
        fixed_output_path = "output/script_media.json"
        with open(fixed_output_path, "w", encoding="utf-8") as f:
            json.dump(media_result, f, ensure_ascii=False, indent=2)

        print(f"媒体生成完成，结果已保存到: {output_file}")
        print(f"同时已更新到: {fixed_output_path}")

    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()
