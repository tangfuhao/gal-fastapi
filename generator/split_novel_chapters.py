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
from workflows.chapter_workflows import ChapterSplitWorkflow

async def split_novel_opening_chapter(content: str, temperature: float = 0.7) -> dict:
    """使用 ChapterSplitWorkflow 直接分割小说章节"""
    client = get_deepseek_client()
    prompt_manager = get_prompt_manager()
    workflow = ChapterSplitWorkflow(client, prompt_manager)
    
    result = await workflow.execute(
        system_prompt="novel_chapter_split_system",
        user_prompt="novel_chapter_split_user",
        prompt_replacements={"content": content}
    )
    return result

def main():
    # 读取小说内容
    with open("data/小说1.txt", "r", encoding="utf-8") as f:
        content = f.read()

    try:
        # 调用章节分割
        print("正在分析小说并分割章节...")
        opening_chapter = asyncio.run(split_novel_opening_chapter(content))

        # 将原文内容添加到每个章节中
        content_lines = content.split('\n')
        for chapter in opening_chapter['chapters']:
            start_line = chapter['chapter_start_line']
            end_line = chapter['chapter_end_line']
            chapter_content = '\n'.join(content_lines[start_line-1:end_line])
            chapter['content'] = chapter_content

        # 保存完整的章节数据（JSON格式)
        json_output_path = "output/novel_chapters.json"
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(opening_chapter, f, ensure_ascii=False, indent=2)

        # 创建输出目录
        output_dir = Path("output/novel_chapters")
        output_dir.mkdir(exist_ok=True)
        
        # 生成输出文件名（使用时间戳）(用于备份)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 保存完整的章节数据（JSON格式) 
        json_output_path = output_dir / f"opening_chapter_{timestamp}.json"
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(opening_chapter, f, ensure_ascii=False, indent=2)
        

        print(f"章节分割完成！")
        print(f"JSON格式结果已保存到: {json_output_path}")

    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()
