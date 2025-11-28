"""
游戏主控制器
整合所有系统，提供完整的游戏体验
"""

import sys
import os
import time

# 添加项目根目录到Python路径
_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

from core.game_engine import GameEngine
from core.world import Position
from entities.player import Player
from entities.npc import NPC, NPCPersonality
from colony.resource import ResourceManager, ResourceType
from colony.building import BuildingManager, BuildingType
from colony.production import ProductionSystem
from systems.quest import QuestManager
from systems.event import EventManager
from ui.console_ui import ConsoleUI
from ai.openai_integration import get_openai_integration
from combat.weapons import get_weapon
from combat.combat_engine import CombatEngine
from utils.logger import get_logger
from utils.config import get_config
from typing import Optional, List


class Game:
    """游戏主控制器"""
    
    def __init__(self):
        """初始化游戏"""
        self.logger = get_logger("Game")
        self.config = get_config()
        
        # 初始化核心系统
        self.engine = GameEngine(config_path="config.json")
        self.ui = ConsoleUI()
        self.openai = get_openai_integration()
        
        # 游戏数据
        self.player: Optional[Player] = None
        self.npcs: List[NPC] = []
        self.resource_manager: Optional[ResourceManager] = None
        self.production_system: Optional[ProductionSystem] = None
        self.building_manager = BuildingManager()
        self.quest_manager = QuestManager()
        self.event_manager = EventManager()
        self.combat_engine = CombatEngine()
        
        # 游戏状态
        self.running = False
        self.game_time = 0.0
        
        # 保存NPC AI引用
        self.npc_ais = {}
    
    def initialize_world(self):
        """初始化游戏世界"""
        self.logger.info("初始化游戏世界...")
        
        # 创建玩家
        self.player = Player(name="玩家", position=Position(500, 500))
        self.engine.add_entity(self.player)
        
        # 创建NPC
        self.npcs = [
            NPC(
                name="村民张三",
                position=Position(600, 500),
                personality=NPCPersonality(
                    traits=["kind", "helpful"],
                    kindness=80,
                    profession="farmer"
                )
            ),
            NPC(
                name="守卫李四",
                position=Position(700, 500),
                personality=NPCPersonality(
                    traits=["brave", "loyal"],
                    aggression=60,
                    loyalty=90,
                    profession="guard"
                )
            ),
            NPC(
                name="商人王五",
                position=Position(400, 500),
                personality=NPCPersonality(
                    traits=["greedy", "clever"],
                    kindness=40,
                    profession="merchant"
                )
            ),
        ]
        
        # 添加NPC到引擎
        for npc in self.npcs:
            self.engine.add_entity(npc)
            # 创建NPC AI（传入战斗引擎）
            from ai.npc_ai import NPCAI
            self.npc_ais[npc] = NPCAI(npc, combat_engine=self.combat_engine)
        
        # 创建初始任务
        self._create_initial_quests()
        
        # 初始化资源管理器
        starting_resources = self.config.get("colony.starting_resources", {})
        resource_dict = {
            ResourceType.FOOD: starting_resources.get("food", 100),
            ResourceType.WOOD: starting_resources.get("wood", 100),
            ResourceType.STONE: starting_resources.get("stone", 50),
            ResourceType.METAL: starting_resources.get("metal", 25)
        }
        self.resource_manager = ResourceManager(resource_dict)
        
        # 创建生产系统
        self.production_system = ProductionSystem(self.resource_manager)
        
        self.logger.info("游戏世界初始化完成")
    
    def _create_initial_quests(self):
        """创建初始任务"""
        if len(self.npcs) > 0:
            # 创建一个击败任务
            kill_quest = self.quest_manager.create_kill_quest(
                quest_id="quest_001",
                title="清理盗贼",
                description="村子附近出现了盗贼，请帮助清理他们。需要击败3个敌人。",
                giver=self.npcs[0],
                kill_count=3,
                reward_gold=200,
                reward_exp=100
            )
            self.quest_manager.add_quest(kill_quest)
            
            # 创建一个收集任务
            collect_quest = self.quest_manager.create_collect_quest(
                quest_id="quest_002",
                title="收集木材",
                description="我们需要更多的木材来建造房屋。请收集10单位木材。",
                giver=self.npcs[0],
                item_type="wood",
                count=10,
                reward_gold=150,
                reward_exp=80
            )
            self.quest_manager.add_quest(collect_quest)
    
    def start(self):
        """启动游戏"""
        self.logger.info("=" * 50)
        self.logger.info("骑砍环世界融合游戏启动")
        self.logger.info("=" * 50)
        
        # 初始化世界
        self.initialize_world()
        
        # 显示欢迎信息
        self.ui.clear_screen()
        self.ui.print_header("欢迎来到骑砍环世界融合游戏！")
        print("\n这是一个融合了《骑马与砍杀》战斗系统和《环世界》管理系统的游戏。")
        print("在这个开放世界中，你可以探索、战斗、建设基地、完成任务。")
        self.ui.wait_for_input("\n按Enter开始游戏...")
        
        # 开始游戏循环
        self.running = True
        self.game_loop()
    
    def game_loop(self):
        """游戏主循环"""
        last_time = time.time()
        
        while self.running:
            # 计算时间增量
            current_time = time.time()
            delta_time = min(current_time - last_time, 0.25)
            last_time = current_time
            self.game_time += delta_time
            
            # 更新游戏系统
            self.update_game_systems(delta_time)
            
            # 显示主菜单并处理玩家输入
            self.handle_main_menu()
            
            # 检查游戏结束条件
            if not self.player.is_alive:
                self.ui.show_message("你死了！游戏结束。")
                self.running = False
                break
    
    def update_game_systems(self, delta_time: float):
        """更新游戏系统"""
        # 更新引擎
        self.engine.update(delta_time)
        
        # 更新NPC AI
        for npc, npc_ai in self.npc_ais.items():
            if npc.is_alive:
                npc_ai.update(delta_time, self.game_time)
        
        # 更新生产系统
        if self.production_system:
            self.production_system.update(delta_time)
        
        # 更新任务系统
        self.quest_manager.update_quests(self.player, delta_time)
        
        # 更新事件系统
        if self.resource_manager:
            self.event_manager.update(delta_time, self.player, self.resource_manager)
    
    def handle_main_menu(self):
        """处理主菜单"""
        self.ui.clear_screen()
        action = self.ui.show_main_menu(self.player)
        
        if action == "explore":
            self.handle_explore()
        elif action == "talk":
            self.handle_talk()
        elif action == "quests":
            self.handle_quests()
        elif action == "colony":
            self.handle_colony()
        elif action == "status":
            self.ui.clear_screen()
            self.ui.show_player_status(self.player)
        elif action == "save":
            self.handle_save()
        elif action == "quit":
            if self.confirm_quit():
                self.running = False
    
    def handle_explore(self):
        """处理探索"""
        self.ui.clear_screen()
        self.ui.print_header("探索")
        
        print("\n你在世界中探索...")
        
        # 随机事件
        import random
        if random.random() < 0.3:
            print("\n你发现了一些资源！")
            if self.resource_manager:
                resource_type = random.choice(list(ResourceType))
                amount = random.randint(5, 15)
                self.resource_manager.add_resource(resource_type, amount)
                print(f"获得了 {amount} 单位 {resource_type.value}")
        else:
            print("\n你探索了一会儿，但没有发现什么特别的东西。")
        
        # 更新位置（简化处理）
        import random
        self.player.position.x += random.randint(-50, 50)
        self.player.position.y += random.randint(-50, 50)
        
        self.ui.wait_for_input()
    
    def handle_talk(self):
        """处理与NPC对话"""
        self.ui.clear_screen()
        
        # 获取附近的NPC
        nearby_npcs = self.get_nearby_npcs()
        
        if not nearby_npcs:
            self.ui.show_message("附近没有NPC。")
            return
        
        # 选择NPC
        npc = self.ui.show_npc_list(nearby_npcs)
        if not npc:
            return
        
        # 对话循环
        while True:
            self.ui.clear_screen()
            action = self.ui.show_npc_dialog(npc, self.player, self.openai)
            
            if action == "leave":
                break
            elif action == "ask_quest":
                self.handle_ask_quest(npc)
            elif action == "view_quests":
                self.handle_view_npc_quests(npc)
            elif action == "trade":
                self.ui.show_message("交易功能即将推出！")
    
    def handle_ask_quest(self, npc: NPC):
        """向NPC询问任务"""
        self.ui.clear_screen()
        self.ui.print_header(f"询问 {npc.name}")
        
        available_quests = [q for q in self.quest_manager.get_available_quests() 
                          if q.giver == npc]
        
        if available_quests:
            print("\n可用的任务:")
            for i, quest in enumerate(available_quests, 1):
                print(f"\n{i}. {quest.title}")
                print(f"   描述: {quest.description}")
                print(f"   奖励: {quest.reward_gold}金币, {quest.reward_exp}经验")
            
            choice = input("\n输入任务编号接受任务（0返回）: ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(available_quests):
                    quest = available_quests[idx]
                    if self.quest_manager.accept_quest(quest.quest_id):
                        self.ui.show_message(f"你接受了任务: {quest.title}")
                    else:
                        self.ui.show_message("接受任务失败。")
            except ValueError:
                pass
        else:
            print("\n当前没有可用的任务。")
        
        self.ui.wait_for_input()
    
    def handle_view_npc_quests(self, npc: NPC):
        """查看NPC的任务"""
        active_quests = [q for q in self.quest_manager.get_active_quests() 
                        if q.giver == npc]
        
        self.ui.clear_screen()
        self.ui.show_quest_list([], active_quests)
    
    def handle_quests(self):
        """处理任务菜单"""
        self.ui.clear_screen()
        
        available = self.quest_manager.get_available_quests()
        active = self.quest_manager.get_active_quests()
        
        self.ui.show_quest_list(available, active)
        
        # 可以在这里添加接受任务的逻辑
        if available:
            choice = input("\n输入任务编号接受任务（0返回）: ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(available):
                    quest = available[idx]
                    if self.quest_manager.accept_quest(quest.quest_id):
                        self.ui.show_message(f"你接受了任务: {quest.title}")
                    else:
                        self.ui.show_message("接受任务失败。")
                    self.ui.wait_for_input()
            except ValueError:
                pass
    
    def handle_colony(self):
        """处理基地管理"""
        while True:
            self.ui.clear_screen()
            action = self.ui.show_colony_menu(self.resource_manager, self.building_manager)
            
            if action == "back":
                break
            elif action == "build":
                self.handle_build()
            elif action == "production":
                self.ui.show_message("生产系统功能完善中...")
    
    def handle_build(self):
        """处理建造"""
        self.ui.clear_screen()
        self.ui.print_header("建造建筑")
        
        print("\n可建造的建筑:")
        building_types = list(BuildingType)
        for i, btype in enumerate(building_types[:5], 1):  # 只显示前5种
            print(f"{i}. {btype.value}")
        
        choice = input("\n选择建筑类型（0返回）: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(building_types[:5]):
                building_type = building_types[idx]
                self.ui.show_message(f"建造 {building_type.value} 功能完善中...")
        except ValueError:
            pass
    
    def handle_save(self):
        """处理保存"""
        self.ui.show_message("保存功能即将推出！")
    
    def get_nearby_npcs(self, radius: float = 200.0) -> List[NPC]:
        """
        获取附近的NPC
        
        Args:
            radius: 搜索半径
            
        Returns:
            附近的NPC列表
        """
        nearby = []
        for npc in self.npcs:
            if not npc.is_alive:
                continue
            distance = self.player.position.distance_to(npc.position)
            if distance <= radius:
                nearby.append(npc)
        return nearby
    
    def run(self):
        """运行游戏"""
        try:
            self.start()
        except KeyboardInterrupt:
            self.logger.info("游戏被用户中断")
            print("\n\n游戏已退出。")
        except Exception as e:
            self.logger.error(f"游戏运行出错: {e}", exc_info=True)
            print(f"\n错误: {e}")
            print("请检查日志文件获取详细信息。")
        finally:
            self.logger.info("游戏结束")




def main():
    """游戏入口"""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()

