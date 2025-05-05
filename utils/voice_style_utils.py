from typing import List, Dict

def format_voice_styles(speaker_voice_style: List[Dict[str, str]]) -> str:
    """
    将 [{'name': ..., 'voice_style': ...}, ...] 格式的数据转换为：
    name:voice_style\nname:voice_style ... 的字符串。
    """
    return "\n".join(f"{item['name']}:{item['voice_style']}" for item in speaker_voice_style if 'name' in item and 'voice_style' in item)
