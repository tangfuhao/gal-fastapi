from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class BackgroundMusicResult:
    """背景音樂生成結果"""
    chapter_index: int
    bgm_name: str
    audio_url: str
    prompt: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None 