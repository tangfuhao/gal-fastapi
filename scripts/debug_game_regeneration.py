import asyncio
import sys
import os
import logging

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

from models.game import DBGame, GameStatus, GameGenerationProgress
from workflows.game_generation import GameGenerationWorkflow
from repositories.json_game_repository import JsonGameRepository, JsonRuntimeGameRepository
from models.types import PyObjectId
from models.game import UserInfo

TEST_GAME_ID = PyObjectId("68109118b1ab4f3c3de2df12")
#打印测试游戏ID
logger.info(f"测试游戏ID: {TEST_GAME_ID}")

async def main():
    # 创建一个 JSON 仓库，每个游戏保存为单独的文件
    game_repo = JsonGameRepository("data/games")
    runtime_game_repo =  JsonRuntimeGameRepository("data/runtime_games")
    
    # 尝试获取已存在的游戏
    game = await game_repo.get(TEST_GAME_ID)
    
    # 如果游戏不存在，创建一个新的
    if not game:
        logger.info("游戏不存在，创建新游戏...")
        game = DBGame(
            id=TEST_GAME_ID,
            title="Test Game",
            input_text="我穿越到明朝成为太子",
            novel_text="""当我遇见他时，我只是一家鸡尾酒吧的女服务员。
他身材高大，皮肤黝黑，英俊潇洒。
他也是这座城市最危险的人。
他也想要我。
当我同意和他约会时，我并不知道自己会陷入什么境地。
只是一个晚上。
一个晚上改变了一切。
一个晚上，我爱上了他。
一个夜晚，让我永远属于他。
但后来我发现我怀孕了。
我知道我必须对他保守这个秘密。
我坐在床边，盯着手中的阳性妊娠测试结果。
我的心在胸腔里怦怦跳动，如同打鼓一般。
怎么会这样呢？
我回想起与这座城市最危险的人利奥·莫雷蒂在一起的那个夜晚。
本来应该只是一个晚上。
一个令人难以置信的、令人难忘的夜晚。
但现在，一切都变了。
我需要和某人谈谈。
我抓起电话，用颤抖的手指拨通了莎拉的号码。
“喂？”电话响了几声后她接了电话。
“莎拉，是我，”我声音颤抖地说，“我需要见你。情况紧急。”
“艾米丽，怎么了？”她问道，语气中明显带着担忧。
“我到了那儿再解释，”我回答道，然后抓起外套朝门口走去。
二十分钟后，我坐在莎拉舒适的客厅里，手里紧紧握着一杯茶，仿佛它是一条生命线。
莎拉坐在我对面，忧虑地睁大了眼睛。
“艾米丽，你吓到我了。发生什么事了？”
我深吸一口气，把验孕棒递给了她。
当她看着它时，她的眼睛睁得更大了。
“哦，我的天哪，”她低声说道，“难道……？”
“是的，”我几乎是低声说道，“是利奥的。”
莎拉脸色一白，“里奥·莫雷蒂？黑手党老大？”
我点点头，眼角隐隐泛泪。“莎拉，我该怎么办？要是他发现了……”
莎拉越过桌子，握住我的手。“你得把孩子藏起来，别让他看到。不能让他知道。”
“可怎么办？”我问道，语气里透着绝望。“他到处都有人。他迟早会发现的。”
“那你就得离开，”莎拉坚定地说，“搬到一个新的城市去。在他找不到你的地方重新开始。”
我慢慢地点了点头，意识到她说得对。“可是我要去哪里？我要怎么活下去？”
“你会成功的，”莎拉坚定地说。“你很坚强，艾米丽。你能做到的。”
与此同时，在城市另一边的豪华豪宅里，莱奥·莫雷蒂正在办公室里来回踱步。
他的手下站在他面前，羞愧地低着头。
“还是没有她的踪迹？”里奥咆哮道，他的沮丧之情溢于言表。
“没有，老大，”其中一个人紧张地说，“我们到处都搜过了。”
利奥一拳砸在桌子上，吓了他们一跳。“继续找！我要找到她！”
当他们匆匆走出房间时，利奥瘫坐在椅子上，双手捂住脸。
他不停地回想与艾米丽在一起的那个夜晚。
她笑的样子，她用那双充满信任的大眼睛看着他的样子。
他以前从来没有过这样的感觉。
现在她已经走了。
他必须找到她。
回到公寓后，我开始收拾东西。
我没什么东西——只有一个装满衣服和一些个人物品的手提箱。
当我拉上行李箱的拉链时，我感到一阵悲伤，因为我要离开在这里建立的生活。
但我知道这是最好的结果。
我不能冒险让利奥发现这个孩子。
最后环顾了一下公寓，我抓起行李箱，朝门口走去。
当我把车票递给司机时，他向我点了点头。
我紧张地环顾四周，观察其他乘客的脸。
他们中的大多数人看上去都很疲惫或者陷入了沉思。
当我走到后面附近的一个空座位时，我的心怦怦直跳。
当公共汽车驶离车站时，我感到一阵既轻松又恐惧。
窗外的城市景观变得模糊，取而代之的是开阔的田野和茂密的森林。
我努力平复自己纷乱的思绪，将注意力集中到发动机有节奏的嗡嗡声上。
几个小时后，我们到达了安静的枫木镇。
这与我离开的繁华城市形成了鲜明的对比。
街道两旁遍布着古色古香的商店和舒适的咖啡馆，空气清新。
我在镇子边缘找到了一家简朴的汽车旅馆，并用假名登记入住。
接待员递给我钥匙时几乎没有看我一眼。
“12号房间，”她用单调的声音说道。
我筋疲力尽地拖着疲惫的身子走进房间，打开了门。
房间虽小但很干净，有一张单人床和一张破旧的扶手椅放在窗边。
我倒在床上，心不在焉地揉着日渐隆起的肚子。
与此同时，Leo 收到了有关我可能行踪的提示。
他坐在办公室里，眯着眼睛听着电话里的线人说话。
“枫林？”他重复道，语气冰冷。“搜查附近每一个小镇。我要找到她。”
他的手下点点头，然后迅速离开去执行他的命令。
我被敲门声吵醒了。
我小心翼翼地走近，心跳加速，担心会发生最坏的情况。
“谁呀？”我大声喊道，尽量保持声音平稳。
“是客房服务，”门的另一边传来回答。
我松了一口气，把门打开了一条缝。
一位年轻女子站在那里，推着一辆装满清洁用品的推车。
“您需要干净的毛巾吗？”她礼貌地微笑着问道。
“不用了，谢谢，”我赶紧回答，“我没事。”
她点点头，然后走向隔壁的房间。
我关上门，靠在门上，试图平稳呼吸。
每一次敲门声、每一张陌生的面孔都让我感到一阵阵焦虑。
我知道利奥不会轻易放弃。
当他想要某样东西或某个人时，他总是坚持不懈。
夜幕降临，我决定出去吃点东西。
汽车旅馆的自动售货机无法提供晚餐。
我穿上一件夹克，走到外面，感受着凉爽的夜晚空气。
街道上很安静，只有零星几个人来来往往。
我在几个街区外找到了一家小餐馆并溜了进去。
空气中弥漫着煎培根和刚煮好的咖啡的香味。
我找了个角落座位坐下，快速浏览了一下菜单。
一位女服务员面带友善的微笑走过来。“请问您需要什么？”
“我要一个芝士汉堡和薯条，”我说道，并把菜单递给她。
“马上就来，”她回答道，然后走回厨房。
当我等待食物时，我总感觉有人在看着我。
我紧张地环顾四周，但没有发现任何异常。
当我的食物送到时，我很快就吃完了，急切地想回到安全的汽车旅馆房间。
回来的路上，我注意到汽车旅馆入口对面停着一辆黑色汽车。
我急忙跑进屋里，心里感到一阵不安。
一进房间，我就锁上了门，并仔细检查了所有的窗户。""",
            user_id=PyObjectId(),
            user_info=UserInfo(
                name="Test User",
                avatar_url="test-avatar.jpg"
            ),
            status=GameStatus.GENERATING,
            progress=GameGenerationProgress(
                current_workflow="",
                completed_workflows=[],
                error_message="Previous error"
            ),
            generate_chapter_index=1
        )
        await game_repo.create(game)
        logger.info(f"创建新游戏成功，ID: {game.id}")
    else:
        logger.info(f"找到已存在的游戏，ID: {game.id}")
    
    # 创建工作流实例
    workflow = GameGenerationWorkflow(game_repo, runtime_game_repo)
    
    logger.info("开始重新生成游戏...")
    logger.info(f"初始状态: {game.status}")
    logger.info(f"当前工作流: {game.progress.current_workflow}")
    
    # 执行重新生成
    await workflow.generate_game(game)
    
    # 获取更新后的游戏
    updated_game = await game_repo.get(game.id)
    
    logger.info("重新生成完成")
    logger.info(f"最终状态: {updated_game.status}")
    if updated_game.error:
        logger.error(f"错误信息: {updated_game.error}")
    if hasattr(updated_game, 'progress'):
        logger.info(f"完成的工作流: {updated_game.progress.completed_workflows}")

if __name__ == "__main__":
    asyncio.run(main())
