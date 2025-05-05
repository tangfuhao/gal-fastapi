import os
import json
import requests
from datetime import datetime
from pathlib import Path

def optimize_novel_chapter(content: str, temperature: float = 0.7) -> dict:
    """调用小说章节优化 API"""
    response = requests.post(
        "http://localhost:8000/optimize-novel-chapter",
        json={"content": content, "temperature": temperature}
    )
    response.raise_for_status()
    json_data = response.json()
    return json_data

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

        print("开始优化章节...")
        print(f"正在优化第一个章节...")
        
        # 调用优化接口
        optimized_result = optimize_novel_chapter(chapter_content)
        
        # 构建完整的优化结果
        optimized_data = {
            "summary": chapters_data['chapters'][0]['summary'],
            "chapter_start_line": chapters_data['chapters'][0]['chapter_start_line'],
            "chapter_end_line": chapters_data['chapters'][0]['chapter_end_line'],
            "original_content": chapter_content,
            "optimized_content": optimized_result["optimized_content"]
        }

        # 保存优化后的章节数据（JSON格式）
        json_output_path = output_dir / f"optimized_chapters_{timestamp}.json"
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(optimized_data, f, ensure_ascii=False, indent=2)

        # 同时更新到固定路径
        fixed_output_path = "output/optimized_chapters.json"
        with open(fixed_output_path, "w", encoding="utf-8") as f:
            json.dump(optimized_data, f, ensure_ascii=False, indent=2)

        print(f"章节优化完成！")
        print(f"JSON格式结果已保存到: {json_output_path}")
        print(f"同时已更新到: {fixed_output_path}")

    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()
