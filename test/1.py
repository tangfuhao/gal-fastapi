import json

# 原始数据（假设已正确解析为JSON对象）
original_data = """
{
    "msg": "获取成功",
    "speakers": {
        "渊武": {
            "中文": [
                "难过_sad",
                "生气_angry",
                "中立_neutral",
                "开心_happy",
                "随机"
            ]
        },
        "布兰特": {
            "中文": [
                "生气_angry",
                "中立_neutral",
                "难过_sad",
                "开心_happy",
                "随机"
            ]
        },
        "小女孩": {
            "中文": [
                "开心_happy",
                "难过_sad",
                "生气_angry",
                "中立_neutral",
                "随机"
            ]
        },
        "炽霞": {
            "中文": [
                "_unk_",
                "中立_neutral",
                "开心_happy",
                "生气_angry",
                "难过_sad",
                "随机"
            ]
        },
        "秧秧": {
            "中文": [
                "中立_neutral",
                "难过_sad",
                "开心_happy",
                "生气_angry",
                "随机"
            ]
        },
        "釉瑚": {
            "中文": [
                "开心_happy",
                "生气_angry",
                "随机"
            ]
        },
        "巴多里奥": {
            "中文": [
                "中立_neutral",
                "生气_angry",
                "开心_happy",
                "随机"
            ]
        },
        "灯灯": {
            "中文": [
                "中立_neutral",
                "生气_angry",
                "开心_happy",
                "难过_sad",
                "随机"
            ]
        },
        "芬莱克": {
            "中文": [
                "难过_sad",
                "中立_neutral",
                "随机"
            ]
        },
        "偃师": {
            "中文": [
                "难过_sad",
                "生气_angry",
                "开心_happy",
                "中立_neutral",
                "随机"
            ]
        },
        "桃祈": {
            "中文": [
                "开心_happy",
                "难过_sad",
                "中立_neutral",
                "随机"
            ]
        },
        "长离": {
            "中文": [
                "开心_happy",
                "生气_angry",
                "难过_sad",
                "中立_neutral",
                "随机"
            ]
        },
        "秋水": {
            "中文": [
                "_unk_",
                "生气_angry",
                "中立_neutral",
                "难过_sad",
                "开心_happy",
                "随机"
            ]
        },
        "散华": {
            "中文": [
                "中立_neutral",
                "难过_sad",
                "生气_angry",
                "随机"
            ]
        },
        "卡卡罗": {
            "中文": [
                "生气_angry",
                "难过_sad",
                "中立_neutral",
                "随机"
            ]
        },
        "守岸人": {
            "中文": [
                "生气_angry",
                "难过_sad",
                "中立_neutral",
                "开心_happy",
                "随机"
            ]
        },
        "维里奈": {
            "中文": [
                "生气_angry",
                "难过_sad",
                "开心_happy",
                "中立_neutral",
                "随机"
            ]
        },
        "奈亚拉": {
            "中文": [
                "开心_happy",
                "难过_sad",
                "随机"
            ]
        },
        "菲比": {
            "中文": [
                "生气_angry",
                "_unk_",
                "开心_happy",
                "难过_sad",
                "中立_neutral",
                "随机"
            ]
        },
        "小盈": {
            "中文": [
                "中立_neutral",
                "生气_angry",
                "难过_sad",
                "_unk_",
                "开心_happy",
                "随机"
            ]
        },
        "洛可可": {
            "中文": [
                "难过_sad",
                "生气_angry",
                "开心_happy",
                "中立_neutral",
                "随机"
            ]
        },
        "莫特斐": {
            "中文": [
                "生气_angry",
                "中立_neutral",
                "难过_sad",
                "开心_happy",
                "随机"
            ]
        },
        "白芷": {
            "中文": [
                "难过_sad",
                "中立_neutral",
                "开心_happy",
                "生气_angry",
                "随机"
            ]
        },
        "吟霖": {
            "中文": [
                "中立_neutral",
                "难过_sad",
                "开心_happy",
                "生气_angry",
                "随机"
            ]
        },
        "「角」": {
            "中文": [
                "开心_happy",
                "难过_sad",
                "中立_neutral",
                "随机"
            ]
        },
        "珂莱塔": {
            "中文": [
                "难过_sad",
                "开心_happy",
                "生气_angry",
                "中立_neutral",
                "随机"
            ]
        },
        "弗洛洛": {
            "中文": [
                "开心_happy",
                "中立_neutral",
                "难过_sad",
                "随机"
            ]
        },
        "今汐": {
            "中文": [
                "中立_neutral",
                "生气_angry",
                "难过_sad",
                "开心_happy",
                "随机"
            ]
        },
        "科波拉": {
            "中文": [
                "生气_angry",
                "开心_happy",
                "中立_neutral",
                "随机"
            ]
        },
        "阿莱克斯司铎": {
            "中文": [
                "生气_angry",
                "中立_neutral",
                "开心_happy",
                "随机"
            ]
        },
        "赞妮": {
            "中文": [
                "生气_angry",
                "难过_sad",
                "中立_neutral",
                "随机"
            ]
        },
        "安可": {
            "中文": [
                "开心_happy",
                "生气_angry",
                "中立_neutral",
                "_unk_",
                "难过_sad",
                "随机"
            ]
        },
        "鉴心": {
            "中文": [
                "开心_happy",
                "中立_neutral",
                "难过_sad",
                "生气_angry",
                "随机"
            ]
        },
        "奇异的白猫": {
            "中文": [
                "难过_sad",
                "中立_neutral",
                "开心_happy",
                "生气_angry",
                "随机"
            ]
        },
        "克里斯托弗": {
            "中文": [
                "生气_angry",
                "开心_happy",
                "中立_neutral",
                "难过_sad",
                "随机"
            ]
        },
        "忌炎": {
            "中文": [
                "生气_angry",
                "开心_happy",
                "中立_neutral",
                "难过_sad",
                "随机"
            ]
        },
        "漂泊者_男": {
            "中文": [
                "生气_angry",
                "开心_happy",
                "难过_sad",
                "中立_neutral",
                "随机"
            ]
        },
        "椿": {
            "中文": [
                "中立_neutral",
                "生气_angry",
                "难过_sad",
                "开心_happy",
                "随机"
            ]
        },
        "禾盈": {
            "中文": [
                "生气_angry",
                "开心_happy",
                "难过_sad",
                "随机"
            ]
        },
        "伤痕": {
            "中文": [
                "生气_angry",
                "中立_neutral",
                "难过_sad",
                "开心_happy",
                "随机"
            ]
        },
        "凌阳": {
            "中文": [
                "生气_angry",
                "开心_happy",
                "中立_neutral",
                "难过_sad",
                "随机"
            ]
        },
        "漂泊者_女": {
            "中文": [
                "中立_neutral",
                "生气_angry",
                "开心_happy",
                "难过_sad",
                "随机"
            ]
        },
        "丹瑾": {
            "中文": [
                "开心_happy",
                "难过_sad",
                "中立_neutral",
                "生气_angry",
                "随机"
            ]
        },
        "贝诗": {
            "中文": [
                "中立_neutral",
                "生气_angry",
                "难过_sad",
                "开心_happy",
                "随机"
            ]
        },
        "折枝": {
            "中文": [
                "难过_sad",
                "开心_happy",
                "生气_angry",
                "中立_neutral",
                "随机"
            ]
        },
        "阿布": {
            "中文": [
                "中立_neutral",
                "开心_happy",
                "难过_sad",
                "_unk_",
                "生气_angry",
                "随机"
            ]
        },
        "辛夷": {
            "中文": [
                "难过_sad",
                "开心_happy",
                "中立_neutral",
                "随机"
            ]
        },
        "文叔": {
            "中文": [
                "中立_neutral",
                "生气_angry",
                "难过_sad",
                "开心_happy",
                "随机"
            ]
        },
        "相里要": {
            "中文": [
                "开心_happy",
                "难过_sad",
                "生气_angry",
                "中立_neutral",
                "随机"
            ]
        },
        "1号演员": {
            "中文": [
                "中立_neutral",
                "开心_happy",
                "难过_sad",
                "生气_angry",
                "随机"
            ]
        }
    }
}
"""

# 解析原始数据
data = json.loads(original_data)
speakers = data['speakers']

# 创建情绪到角色的映射（排除"随机"）
emotion_to_speakers = {}

for speaker_name, speaker_info in speakers.items():
    for emotion in speaker_info['中文']:
        if emotion == "随机":
            continue  # 跳过随机
        if emotion not in emotion_to_speakers:
            emotion_to_speakers[emotion] = []
        emotion_to_speakers[emotion].append(speaker_name)

# 转换为所需的JSON对象数组格式
result = [
    {
        "mood": emotion,
        "speakers": speakers_list
    }
    for emotion, speakers_list in emotion_to_speakers.items()
]

# 输出结果
print(json.dumps(result, ensure_ascii=False, indent=2))