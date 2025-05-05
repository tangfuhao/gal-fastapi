from enum import Enum
from typing import List, Union, Optional, Dict, Any
from dataclasses import dataclass, asdict
from pydantic import BaseModel

class CommandType(str, Enum):
    """指令类型枚举"""
    NARRATION = "narration"
    DIALOGUE = "dialogue"
    CHOICE = "choice"
    JUMP = "jump"
    BG = "bg"
    BGM = "bgm"

@dataclass
class BaseCommand:
    """基础指令类"""
    type: CommandType

    def model_dump(self) -> Dict[str, Any]:
        """转换为字典，用于MongoDB序列化"""
        data = asdict(self)
        data['type'] = self.type.value
        return data

@dataclass
class NarrationCommand(BaseCommand):
    """旁白指令"""
    text: str

    def __init__(self, text: str):
        super().__init__(CommandType.NARRATION)
        self.text = text

@dataclass
class DialogueCommand(BaseCommand):
    """对话指令"""
    character: str
    emotion: str
    text: str
    target: Optional[str] = None

    def __init__(self, character: str, emotion: str, text: str, target: Optional[str] = None):
        super().__init__(CommandType.DIALOGUE)
        self.character = character
        self.emotion = emotion
        self.text = text
        self.target = target

@dataclass
class ChoiceCommand(BaseCommand):
    """选项指令"""
    text: str
    target: str

    def __init__(self, text: str, target: str):
        super().__init__(CommandType.CHOICE)
        self.text = text
        self.target = target

@dataclass
class JumpCommand(BaseCommand):
    """跳转指令"""
    target: str

    def __init__(self, target: str):
        super().__init__(CommandType.JUMP)
        self.target = target

@dataclass
class BackgroundCommand(BaseCommand):
    """背景指令"""
    name: str
    prompt: str

    def __init__(self, name: str, prompt: str):
        super().__init__(CommandType.BG)
        self.name = name
        self.prompt = prompt

@dataclass
class BGMCommand(BaseCommand):
    """背景音乐指令"""
    name: str
    prompt: str

    def __init__(self, name: str, prompt: str):
        super().__init__(CommandType.BGM)
        self.name = name
        self.prompt = prompt

@dataclass
class Branch:
    """分支数据类"""
    name: str
    commands: List[Union[NarrationCommand, DialogueCommand, ChoiceCommand, JumpCommand, BackgroundCommand, BGMCommand]]

    def model_dump(self) -> Dict[str, Any]:
        """转换为字典，用于MongoDB序列化"""
        return {
            "name": self.name,
            "commands": [cmd.model_dump() for cmd in self.commands]
        }

# 类型别名
Command = Union[NarrationCommand, DialogueCommand, ChoiceCommand, JumpCommand, BackgroundCommand, BGMCommand]

# 错误类定义
class ScriptValidationError(Exception):
    """脚本验证基础错误类"""
    pass

class BranchError(ScriptValidationError):
    """分支相关错误"""
    pass

class CommandError(ScriptValidationError):
    """指令相关错误"""
    pass

class StructureError(ScriptValidationError):
    """结构相关错误"""
    pass

class DialogueDensityError(ScriptValidationError):
    """对话密度错误"""
    pass
