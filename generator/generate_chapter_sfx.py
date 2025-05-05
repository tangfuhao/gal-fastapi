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
from workflows.sfx_workflows import SFXGenerationWorkflow

async def generate_sfx_stable_audio(content: str, sfx: str, temperature: float = 0.7) -> dict:
    """使用 SFXGenerationWorkflow 直接生成音效"""
    client = get_deepseek_client()
    prompt_manager = get_prompt_manager()
    workflow = SFXGenerationWorkflow(client, prompt_manager)
    
    result = await workflow.execute(
        system_prompt="sfx_stable_audio_system",
        user_prompt="sfx_stable_audio_user",
        prompt_replacements={"content": content, "sfx": sfx}
    )
    return result

def main():
    # 读取优化后的脚本
    with open("output/optimized_chapters.json", "r", encoding="utf-8") as f:
        optimized_chapters = json.load(f)

    try:
        # 创建输出目录
        output_dir = Path("output/sfx")
        output_dir.mkdir(exist_ok=True)
        
        # 生成输出文件名（使用时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 获取第一个章节的内容和sfx
        chapter_content = optimized_chapters['content']
        chapter_sfx = optimized_chapters.get('sfx', '')

        print("开始生成音效...")
        sfx_result = asyncio.run(generate_sfx_stable_audio(
            content=chapter_content,
            sfx=chapter_sfx
        ))

        # 保存结果
        output_file = output_dir / f"sfx_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(sfx_result, f, ensure_ascii=False, indent=2)
            
        print(f"音效生成完成，结果已保存到: {output_file}")

    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()
