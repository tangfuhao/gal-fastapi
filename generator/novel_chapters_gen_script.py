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
from workflows.script_workflows import ScriptGenerationWorkflow

async def generate_novel_chapter_script(content: str, temperature: float = 0.7) -> str:
    """使用 ScriptGenerationWorkflow 直接生成小说章节脚本"""
    client = get_deepseek_client()
    prompt_manager = get_prompt_manager()
    workflow = ScriptGenerationWorkflow(client, prompt_manager)
    
    result = await workflow.execute(
        system_prompt="novel_chapter_script_system",
        user_prompt="novel_chapter_script_user",
        prompt_replacements={"content": content}
    )
    return result

def main():
    # 读取章节数据
    with open("output/novel_chapters.json", "r", encoding="utf-8") as f:
        chapters_data = json.load(f)

    try:
        # 创建输出目录
        output_dir = Path("output/optimized_chapters")
        output_dir.mkdir(exist_ok=True)
        
        # 生成输出文件名（使用时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 获取第一个章节的内容
        chapter_content = chapters_data['chapters'][0]['content']

        print("开始生成脚本...")
        print(f"正在生成第一个章节的脚本...")

        first_chapter = chapters_data['chapters'][0]
        
        # 调用脚本生成接口
        script_result = asyncio.run(generate_novel_chapter_script(chapter_content, temperature=0.5))        
        format_script = script_result.strip("'").strip('"')
        first_chapter['script'] = format_script

        # 保存优化后的章节数据（JSON格式）
        json_output_path = output_dir / f"optimized_chapters_{timestamp}.json"
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(first_chapter, f, ensure_ascii=False, indent=2)

        # 同时更新到固定路径
        fixed_output_path = "output/optimized_chapters.json"
        with open(fixed_output_path, "w", encoding="utf-8") as f:
            json.dump(first_chapter, f, ensure_ascii=False, indent=2)

        print(f"章节优化完成！")
        print(f"JSON格式结果已保存到: {json_output_path}")
        print(f"同时已更新到: {fixed_output_path}")

    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()
