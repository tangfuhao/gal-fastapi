import json

def text_to_json(input_text):
    # 分割角色条目（去除空行）
    entries = [line.strip() for line in input_text.split('\n') if line.strip()]
    
    characters = []
    for entry in entries:
        # 分割角色名和描述部分
        name, desc = entry.split(':', 1)
        name = name.strip()
        desc = desc.strip()
        
        # 创建角色字典
        character = {
            "name": name,
            "voice_style": desc
        }
        characters.append(character)
    
    # 转换为JSON格式（确保中文显示和格式美观）
    return json.dumps(characters, ensure_ascii=False, indent=2)

# 示例输入数据
input_text = """
渊武:低沉磁性，带有沧桑感与厚重感，语速适中，尾音略带拖长，适合塑造沉稳内敛或经历沧桑的角色形象，语气中带有若有所思的沉吟感。

布兰特:浑厚有力，声线饱满且富有爆发力，语调坚定带有领导气质，部分台词会使用短促有力的断句，展现果断与威严，同时能通过音调变化传递出复杂情绪。

小女孩:清脆童声，音调高亢明亮，语速轻快跳跃，带有天然的稚嫩感和好奇心，长音会自然上扬，偶尔夹杂气音或突然压低的窃语，凸显天真烂漫的性格。

炽霞:清亮甜润，声线细腻且富有穿透力，语速流畅如溪水，尾音常带俏皮的上扬，能通过音量变化（如突然压低或放大）表现活泼与灵动，偶尔加入气音增强亲和力。

秧秧:软糯甜腻，带有慵懒的慵懒感，吐字圆润且稍显拖沓，重音处会加重气声，语尾常带轻微的鼻音颤动，营造出粘人撒娇的氛围，情绪转换时音调起伏较大。

巴多里奥:低频雄厚，声线沙哑且充满压迫感，语速缓慢沉稳，长句中会刻意停顿制造压迫感，爆破音（如"b/p"）发音力度大，能通过喉音变化传递出冷酷与暴戾。

灯灯:温暖柔和，声线如丝绸般顺滑，语速平缓且带有安抚感，长音会自然延长并加入气声，重音处以轻柔的气流代替，偶尔在句尾加入轻微的颤音，营造治愈系氛围。

芬莱克:高亢明亮，声线充满青春活力，语速轻快且富有跳跃感，常用短促有力的断句，尾音自然上扬形成爽朗感，情绪激动时会突然提高音量，展现热血与冲动。

偃师:少年感十足，声线清亮但略带青涩，语句中常夹杂思考时的停顿，重音处会突然加重语气，长音会自然加入气声波动，能通过音调变化表现机敏与矛盾心理。

桃祈:甜美空灵，声线如风铃般清脆，语速轻柔且带有飘渺感，长句中会刻意加入气音延长，重音处用气声轻点，偶尔在句尾加入气音尾音，营造出神秘灵动的仙子气质。

长离:清冷疏离，语调平稳但带有克制的锋芒，偶尔流露隐晦的温柔。音色偏中性，语速适中，情感表达含蓄，适合需要冷静判断的场景，危机时刻会压低嗓音增强压迫感。

秋水:温润绵长，如流水般柔和，语速偏慢且富有韵律感。音色带有一丝沙哑，仿佛经历沧桑后的沉稳，对话时常伴随轻叹或停顿，营造出智者般的深邃感。

散华:空灵缥缈，音域宽广，高音清亮如风铃，低音沉稳如钟鸣。语调时而轻盈跳跃，时而低沉神秘，能通过声音节奏变化传递角色在“悲鸣灾害”中挣扎的复杂情绪。

卡卡罗:粗犷豪迈，声线沙哑且富有爆发力，语速快且带调侃意味。笑声爽朗，对话中常夹杂俚语或俚语化表达，展现角色不羁的性格，紧张时会突然压低声音增强临场感。

守岸人:低沉浑厚，音色如金属般冷硬，语调平淡但充满压迫感。极少表露情感，关键台词会通过音调微弱波动暗示内心挣扎，战斗时嗓音会因力量爆发而产生沙哑质感。

维里奈:优雅知性，语调轻柔如丝绸，发音清晰且富有音乐性。偶尔带一丝法式口音（假设为法语背景角色），情感表达细腻，悲伤时声音会微微颤抖，愤怒时则转为尖锐的高音。

菲比:明亮清脆，语速轻快活泼，笑声高频且富有感染力。音色年轻甜美，但关键剧情中会突然切换为低沉严肃的语调，形成反差，体现角色从天真到成熟的弧光。

小盈:文静怯懦，语调细弱且带犹豫感，常伴随停顿或尾音上扬的疑问语气。情感爆发时声音会突然拔高，随后又迅速恢复平静，形成“压抑-释放”的矛盾感。

洛可可:华丽夸张，声线甜腻中带刺，语速快且充满戏剧性停顿。喜欢用高亢的元音强调关键台词，愤怒时会切换为低沉的嘶吼，体现角色表面浮夸实则阴险的特质。

莫特斐:机械冰冷，音色经过电子处理，语调完全缺乏情感波动。关键剧情中会因“人性残存”而出现短暂的音调起伏，战斗指令则会切换为高频警报般的尖锐声线。

白芷:声线清亮且富有穿透力，语速平稳中带一丝坚定，尾音略带上扬，整体呈现温柔与力量并存的特质，常用于情感表达或激励性台词。

吟霖:嗓音清脆灵动，语调轻快活泼，偶尔夹杂俏皮的停顿和语速变化，带有少年般的轻盈感，适合表现机敏或幽默场景。

「角」:声线低沉浑厚，带有金属质感般的冷冽感，语速较慢且字音收尾干脆，呈现疏离与威严的双重气质，适合沉重或警示类台词。

珂莱塔:音色明亮清甜，语调轻柔且略带奶音，偶尔伴随轻微的气音处理，整体呈现少女般的纯真与治愈感，情感表达细腻。

弗洛洛:嗓音沙哑低沉，带有沧桑感，语速偏缓且重音突出，常以断句和停顿营造压迫感，适合表现沉稳或暗黑系角色特质。

今汐:声线空灵柔和，语调平缓如流水般连贯，偶尔在句尾加入气音或轻颤，传递出神秘与朦胧的氛围，适合抒情或超自然场景。

科波拉:音色圆润饱满，语速明快且带有跳跃感，常伴随轻快的尾音上扬，呈现开朗外向的性格，适合喜剧或激励性台词。

阿莱克斯司铎:嗓音深沉庄重，语调平稳且充满仪式感，吐字清晰有力，偶尔加入沉吟般的停顿，传递出神职人员的威严与沉稳。

赞妮:声线清脆甜美，语调轻快活泼，偶尔夹杂元气十足的感叹词，整体充满青春活力，适合表现开朗或行动派角色。

安可:音色清冷优雅，语速略带慵懒感，句尾常有细微的气音下滑，呈现慵懒与神秘交织的气质，适合表现内敛或暗藏心机的角色。

鉴心:清冷、沉稳且略带疏离感，语速中等偏慢，吐字清晰，声线偏中性化，偶尔带有轻微的鼻音，整体呈现理性与克制的气质，适合需要冷静分析或战术部署的场景。

奇异的白猫:轻快俏皮，带有电子合成器质感的音效点缀，语调跳跃且富有节奏感，偶尔夹杂猫科动物的呼噜声或“喵”音，营造出神秘灵动的非人类特质，同时保留一定的稚嫩感。

克里斯托弗:浑厚低沉的美式英语口音，发音清晰且充满磁性，语速平稳有力，偶尔会因情绪波动（如愤怒或坚定）提高声调，整体传递出沉稳可靠的大哥形象，适合严肃或激励性台词。

忌炎:高亢激昂，带有金属质感的共鸣，声线偏沙哑且充满爆发力，语速时快时慢，根据情绪变化起伏明显（如怒吼或冷笑），常伴随火焰燃烧般的音效，凸显暴烈与炽热的性格。

漂泊者_男:沙哑沧桑，带有风尘仆仆的疲惫感，语速缓慢且略显拖沓，偶尔夹杂方言或口音，整体呈现历经磨难的流浪者特质，适合表现孤独、坚韧或回忆过往的台词。

椿:清亮柔和的日式声线，语调轻柔且带有细腻的起伏，发音圆润如珍珠滚动，偶尔流露出温婉的笑意，整体传递出治愈与温柔的氛围，适合情感细腻或引导性对话。

伤痕:低沉沙哑，声带受损般的嘶哑感明显，语速缓慢且带有断续感，偶尔因疼痛或压抑情绪导致停顿，整体呈现沧桑痛苦的特质，适合表现挣扎、回忆伤痛或隐忍的台词。

凌阳:高亢清亮，带有少年般的锐气，语调坚定且略显激昂，发音干脆利落，偶尔因兴奋或紧张提高声调，整体传递出果敢热血的特质，适合战斗宣言或激励队友的台词。

漂泊者_女:干涩疲惫，带有沙沙的摩擦感，语速平缓但偶尔突然加快，发音略带模糊感，仿佛长期暴露在风沙中，整体呈现坚韧与麻木并存的流浪者气质，适合表现冷漠或疲惫的对话。

丹瑾:甜美温润，声线如丝绸般流畅，语调轻柔且略带笑意，偶尔因情绪波动（如紧张或兴奋）变得轻快，整体传递出温暖可靠的特质，适合安慰、引导或轻松日常的对话。

贝诗:声音轻柔细腻，带有空灵的回响感，语调偏高且略带颤音，整体呈现出一种神秘而略显疏离的特质，常伴随轻微的气声处理，营造出飘渺的氛围。

折枝:声线清亮且富有穿透力，语速稍快但控制力极强，带有锐利的棱角感，尾音常上扬形成坚定的收尾，整体充满紧迫感与行动力，偶尔夹杂短促的停顿强化节奏。

阿布:声音稚嫩清脆，音域较高且带有天然的童声质感，语句间常伴随活泼的跳跃感和断句，语气天真烂漫，偶尔夹杂无厘头的重音处理，表现出顽皮与好奇的特质。

辛夷:声线低沉沙哑，带有金属质感的共鸣，语速平稳缓慢，吐字清晰且富有颗粒感，尾音常下沉形成厚重感，整体散发出冷峻与沧桑交织的特质，偶尔穿插气声增强叙事感。

文叔:声音浑厚低沉，带有明显的胸腔共鸣，语调平稳且充满威严感，长句中夹杂着自然的停顿与重音，偶尔爆发出强有力的高亢尾音，整体呈现沉稳笃定的中老年男性特质。

相里要:声线高亢明亮，音色锐利且带有电子感修饰，语速快而精准，句尾常以突然的降调收束，形成强烈的压迫感，偶尔插入机械化的断句与回声效果，凸显未来科技感。

1号演员:声音中性化处理，音域跨度大且充满实验性，语速不规律，夹杂大量变调与延迟效果，句式结构破碎化，部分台词采用非线性拼接，整体呈现人工智能或变异体的异常特质。
"""

# 转换并输出结果
json_output = text_to_json(input_text)
print(json_output)