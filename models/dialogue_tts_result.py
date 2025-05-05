from dataclasses import dataclass
from typing import Optional
from utils.script_coder import DialogueCommand

@dataclass
class DialogueTTSResult:
    """對話TTS生成結果"""
    chapter_index: int
    dialogue: DialogueCommand
    success: bool
    audio_url: Optional[str] = None
    error: Optional[str] = None 