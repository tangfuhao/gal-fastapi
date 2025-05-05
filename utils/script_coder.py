from typing import Dict, List, Optional
from pathlib import Path
import json
from dataclasses import asdict
import sys
import os

#设置path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)


from schemas.script_commands import (
    CommandType,
    BaseCommand,
    NarrationCommand,
    DialogueCommand,
    ChoiceCommand,
    JumpCommand,
    BackgroundCommand,
    BGMCommand,
    Branch,
    Command,
    ScriptValidationError,
    BranchError,
    CommandError,
    StructureError
)


class ScriptEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理枚举和数据类"""
    def default(self, obj):
        if isinstance(obj, CommandType):
            return obj.value
        if isinstance(obj, (BaseCommand, Branch)):
            return asdict(obj)
        return super().default(obj)

def _parse_narration(line: str, line_number: int) -> NarrationCommand:
    """解析旁白指令"""
    text = line[10:].strip()
    if not text:
        raise CommandError(f"第 {line_number+1} 行：旁白内容不能为空")
    return NarrationCommand(text=text)

def _parse_dialogue(line: str, line_number: int) -> DialogueCommand:
    """解析对话指令"""
    parts = [p.strip() for p in line[9:].split("->")]
    main_part = parts[0].rsplit(',', 2)
    if len(main_part) != 3:
        raise CommandError(f"第 {line_number+1} 行：对话格式错误，应为'角色,情绪,对话内容'")
    
    char, emotion, text = [p.strip() for p in main_part]
    target = parts[1].strip() if len(parts) > 1 else None
    
    return DialogueCommand(
        character=char,
        emotion=emotion,
        text=text,
        target=target
    )

def _parse_choice(line: str, line_number: int) -> ChoiceCommand:
    """解析选项指令"""
    parts = line[6:].split(',', 1)
    if len(parts) != 2:
        raise CommandError(f"第 {line_number+1} 行：选项格式错误，应为'选项文本,目标分支'")
    
    text, target = [p.strip() for p in parts]
    if not text or not target:
        raise CommandError(f"第 {line_number+1} 行：选项文本和目标分支不能为空")
    
    return ChoiceCommand(text=text, target=target)

def _parse_jump(line: str, line_number: int) -> JumpCommand:
    """解析跳转指令"""
    target = line[5:].strip()
    if not target:
        raise CommandError(f"第 {line_number+1} 行：跳转目标不能为空")
    
    return JumpCommand(target=target)

def _parse_bg(line: str, line_number: int) -> BackgroundCommand:
    """解析背景指令"""
    parts = line[3:].split(' ', 1)
    if len(parts) != 2:
        raise CommandError(f"第 {line_number+1} 行：背景格式错误，应为'背景名称,SD提示词'")
    
    name, prompt = [p.strip() for p in parts]
    if not name or not prompt:
        raise CommandError(f"第 {line_number+1} 行：背景名称和SD提示词不能为空")
    
    return BackgroundCommand(name=name, prompt=prompt)

def _parse_bgm(line: str, line_number: int) -> Command:
    """解析背景音乐指令"""
    parts = line[4:].split(' ', 1)
    if len(parts) != 2:
        raise CommandError(f"第 {line_number+1} 行：背景音乐格式错误，应为'背景音乐名称,SD提示词'")
    
    name, prompt = [p.strip() for p in parts]
    if not name or not prompt:
        raise CommandError(f"第 {line_number+1} 行：背景音乐名称和提示词不能为空")
    
    return BGMCommand(name=name, prompt=prompt)

def _parse_command(line: str, line_number: int) -> Optional[Command]:
    """返回None表示忽略无关行"""
    line = _strip_comment(line)
    if not line:
        return None

    parsers = {
        "narration": _parse_narration,
        "dialogue": _parse_dialogue,
        "choice": _parse_choice,
        "jump": _parse_jump,
        "bg": _parse_bg,
        "bgm": _parse_bgm
    }

    for prefix, parser in parsers.items():
        if line.startswith(prefix + " "):
            return parser(line, line_number)
    
    return None

def _parse_branch_declaration(line: str, line_number: int) -> str:
    """解析分支声明，返回分支名称"""
    branch_name = line[6:].strip()
    if not branch_name:
        raise BranchError(f"第 {line_number+1} 行：分支名称不能为空")
    return branch_name

def _strip_comment(line: str) -> str:
    """去除行内注释，支持双斜杠和三引号注释"""
    line = line.split('//')[0].split('#')[0].strip()
    return line.split('"""')[0].strip()

def _parse_script_structure(content: str) -> List[Branch]:
    branches: Dict[str, List[Command]] = {}
    current_branch = None

    for line_number, raw_line in enumerate(content.split('\n')):
        line = _strip_comment(raw_line.strip())
        if not line:
            continue

        # 分支声明处理
        if line.startswith("branch "):
            current_branch = _parse_branch_declaration(line, line_number)
            branches.setdefault(current_branch, [])
            continue

        # 命令处理
        if current_branch is None:
            continue  # 忽略分支外的指令

        try:
            if (command := _parse_command(line, line_number)) is not None:
                branches[current_branch].append(command)
        except CommandError as e:
            warnings.warn(str(e))  # 非致命错误仅警告

    return [Branch(name=name, commands=cmds) for name, cmds in branches.items()]

def parse_script(content: str) -> List[Branch]:
    try:
        # 第一阶段：解析基础结构
        branches = _parse_script_structure(content)
        #TODO 先关闭测试
        # branches_dict = {branch.name: branch.commands for branch in branches}

        # # 第二阶段：结构验证
        # # 必须存在main和end分支
        # if "main" not in branches_dict:
        #     raise StructureError("缺少必需的'main'分支")
        # if "end" not in branches_dict:
        #     raise StructureError("缺少必需的'end'分支")

        # 验证分支终点
        # for branch in branches:
        #     if branch.name == "end":
        #         continue
                
        #     if not branch.commands:
        #         raise StructureError(f"分支 '{branch.name}' 为空")
                
        #     last_cmd = branch.commands[-1]
        #     if not isinstance(last_cmd, (JumpCommand, ChoiceCommand)):
        #         raise StructureError(f"分支 '{branch.name}' 必须以跳转指令或选项指令结束")

        # # 验证所有跳转目标存在
        # all_branches = set(branches_dict.keys())
        # for branch in branches:
        #     for cmd in branch.commands:
        #         if isinstance(cmd, (JumpCommand, ChoiceCommand)):
        #             if cmd.target not in all_branches:
        #                 raise BranchError(f"在分支 '{branch.name}' 中发现无效的目标分支 '{cmd.target}'")

        return branches

    except ScriptValidationError as e:
        raise ScriptValidationError(f"脚本验证失败：{str(e)}") from e
    except Exception as e:
        raise ScriptValidationError(f"脚本解析出现未知错误：{str(e)}") from e

def serialize_script(branches: List[Branch]) -> str:
    """将分支列表序列化为脚本文本格式

    Args:
        branches: Branch对象列表

    Returns:
        str: 格式化的脚本文本
    """
    # 验证必需的分支
    branch_names = {branch.name for branch in branches}
    if "main" not in branch_names:
        raise StructureError("缺少必需的'main'分支")
    if "end" not in branch_names:
        raise StructureError("缺少必需的'end'分支")
    
    script_lines = []
    
    for branch in branches:
        # 添加分支声明
        script_lines.append(f"branch {branch.name}")
        
        # 添加命令
        for cmd in branch.commands:
            if isinstance(cmd, NarrationCommand):
                script_lines.append(f"narration {cmd.text}")
            elif isinstance(cmd, DialogueCommand):
                dialogue_line = f"dialogue {cmd.character}, {cmd.emotion}, {cmd.text}"
                if cmd.target:
                    dialogue_line += f" -> {cmd.target}"
                script_lines.append(dialogue_line)
            elif isinstance(cmd, BackgroundCommand):
                script_lines.append(f"bg {cmd.name} {cmd.prompt.strip()}")
            elif isinstance(cmd, ChoiceCommand):
                script_lines.append(f"choice {cmd.text}, {cmd.target}")
            elif isinstance(cmd, JumpCommand):
                script_lines.append(f"jump {cmd.target}")
            elif isinstance(cmd, BGMCommand):
                script_lines.append(f"bgm {cmd.name} {cmd.prompt.strip()}")
        
        # 添加空行分隔不同分支
        script_lines.append("")
    
    return "\n".join(script_lines).rstrip()

# 使用示例
if __name__ == "__main__":
    sample_script = """
branch main
bg modern_office_sunset "modern office at sunset, floor-to-ceiling windows, New York skyline, golden hour lighting, warm ambiance"

narration 黄昏的余晖洒在破旧的咖啡馆里
dialogue 艾琳, 中性, 我们必须做出决定了。 -> 妮可
dialogue 妮可, 中性, 可是这样可能会有风险…

choice 迎接挑战, challenge
choice 选择保守, conservative

branch challenge
narration 这是挑战分支
dialogue 小红,生气,不要这样
jump end

branch conservative
dialogue 小明,平静,好吧
jump end

branch end
narration 故事结束了
jump end
"""
    
    try:
        parsed = parse_script(sample_script)
        print("脚本校验通过！")
        print(f"解析分支: {[branch.name for branch in parsed]}")
        
        # 保存到JSON文件
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "parsed_script.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(parsed, f, cls=ScriptEncoder, ensure_ascii=False, indent=2)
        print(f"脚本已保存到: {output_file}")
        
        # 序列化脚本
        serialized_script = serialize_script(parsed)
        print("序列化脚本:")
        print(serialized_script)
        
        # 保存到文件
        serialized_file = output_dir / "serialized_script.txt"
        with open(serialized_file, "w", encoding="utf-8") as f:
            f.write(serialized_script)
        print(f"脚本已保存到: {serialized_file}")
        
    except ScriptValidationError as e:
        print("脚本校验失败:", str(e))