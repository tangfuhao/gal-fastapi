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
from workflows.script_background_workflows import ScriptBackgroundWorkflow

async def generate_script_bgm(script: str, temperature: float = 0.7) -> dict:
    """使用 ScriptBackgroundWorkflow 直接生成BGM"""
    client = get_deepseek_client()
    prompt_manager = get_prompt_manager()
    workflow = ScriptBackgroundWorkflow(client, prompt_manager)
    
    result = await workflow.execute(
        system_prompt="novel_script_bgm_system",
        user_prompt="novel_script_bgm_user",
        prompt_replacements={"script": script}
    )
    return result

def main():
    # 读取优化后的脚本
    with open("output/script_background.json", "r", encoding="utf-8") as f:
        optimized_chapters = json.load(f)

    try:
        # 创建输出目录
        output_dir = Path("output/script_bgm")
        output_dir.mkdir(exist_ok=True)
        
        # 生成输出文件名（使用时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 获取脚本内容
        script_content = optimized_chapters['script_background']

        print("开始生成脚本背景音乐...")
        bgm_result = asyncio.run(generate_script_bgm(
            script=script_content
        ))

        optimized_chapters['script_bgm'] = bgm_result
        
        # 保存结果
        json_output_path = output_dir / f"script_bgm_{timestamp}.json"
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(optimized_chapters, f, ensure_ascii=False, indent=2)

        # 同时更新到固定路径
        fixed_output_path = "output/script_bgm.json"
        with open(fixed_output_path, "w", encoding="utf-8") as f:
            json.dump(optimized_chapters, f, ensure_ascii=False, indent=2)

        print(f"脚本背景音乐生成完成！")
        print(f"JSON格式结果已保存到: {json_output_path}")
        print(f"同时已更新到: {fixed_output_path}")

    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()
