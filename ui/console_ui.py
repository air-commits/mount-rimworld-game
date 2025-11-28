"""
命令行界面系统
提供交互式命令行菜单
"""

from dataclasses import dataclass
from typing import List, Callable, Optional
from enum import Enum

from entities.player import Player
from entities.npc import NPC
from systems.quest import Quest
from systems.event import GameEvent
from utils.logger import get_logger


@dataclass
class MenuOption:
    """菜单选项"""
    key: str                 # 按键
    text: str                # 显示文本
    action: Callable         # 执行函数
    enabled: bool = True     # 是否启用


class ConsoleUI:
    """命令行用户界面"""
    
    def __init__(self):
        """初始化命令行界面"""
        self.logger = get_logger("ConsoleUI")
        self.current_menu: Optional[str] = None
    
    def clear_screen(self):
        """清屏"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str):
        """
        打印标题
        
        Args:
            title: 标题文本
        """
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)
    
    def print_separator(self):
        """打印分隔线"""
        print("-" * 60)
    
    def wait_for_input(self, prompt: str = "\n按Enter继续..."):
        """
        等待用户输入
        
        Args:
            prompt: 提示文本
        """
        input(prompt)
    
    def get_user_choice(self, options: List[MenuOption], prompt: str = "请选择: ") -> Optional[MenuOption]:
        """
        获取用户选择
        
        Args:
            options: 选项列表
            prompt: 提示文本
            
        Returns:
            选中的选项（如果有效）
        """
        # 显示选项
        print()
        for option in options:
            if option.enabled:
                print(f"  [{option.key}] {option.text}")
            else:
                print(f"  [{option.key}] {option.text} (不可用)")
        
        # 获取输入
        choice = input(f"\n{prompt}").strip().lower()
        
        # 查找匹配的选项
        for option in options:
            if option.key.lower() == choice and option.enabled:
                return option
        
        print("无效的选择，请重试。")
        return None
    
    def show_main_menu(self, player: Player) -> Optional[str]:
        """
        显示主菜单
        
        Args:
            player: 玩家对象
            
        Returns:
            选择的动作
        """
        self.print_header("主菜单")
        
        print(f"\n玩家: {player.name} (Lv.{player.level})")
        print(f"生命值: {player.current_health}/{player.max_health}")
        print(f"金币: {player.money}")
        print(f"位置: ({player.position.x:.0f}, {player.position.y:.0f})")
        
        options = [
            MenuOption("1", "探索", lambda: "explore"),
            MenuOption("2", "与NPC对话", lambda: "talk"),
            MenuOption("3", "查看任务", lambda: "quests"),
            MenuOption("4", "基地管理", lambda: "colony"),
            MenuOption("5", "查看状态", lambda: "status"),
            MenuOption("6", "保存游戏", lambda: "save"),
            MenuOption("0", "退出游戏", lambda: "quit")
        ]
        
        choice = self.get_user_choice(options)
        if choice:
            return choice.action()
        return None
    
    def show_player_status(self, player: Player):
        """
        显示玩家状态
        
        Args:
            player: 玩家对象
        """
        self.print_header("玩家状态")
        
        print(f"\n姓名: {player.name}")
        print(f"等级: {player.level}")
        print(f"经验值: {player.experience} / {player.level * 100}")
        print(f"生命值: {player.current_health} / {player.max_health}")
        print(f"金币: {player.money}")
        print(f"声望: {player.reputation}")
        
        print("\n属性:")
        stats = player.stats
        print(f"  力量: {stats.strength}")
        print(f"  敏捷: {stats.dexterity}")
        print(f"  体质: {stats.constitution}")
        print(f"  智力: {stats.intelligence}")
        print(f"  感知: {stats.wisdom}")
        print(f"  魅力: {stats.charisma}")
        
        print(f"\n位置: ({player.position.x:.0f}, {player.position.y:.0f})")
        
        self.wait_for_input()
    
    def show_quest_list(self, quests: List[Quest], active_quests: List[Quest]):
        """
        显示任务列表
        
        Args:
            quests: 可用任务列表
            active_quests: 进行中的任务列表
        """
        self.print_header("任务列表")
        
        if active_quests:
            print("\n【进行中的任务】")
            for i, quest in enumerate(active_quests, 1):
                print(f"\n{i}. {quest.title}")
                print(f"   描述: {quest.description}")
                print(f"   发布者: {quest.giver.name if quest.giver else '未知'}")
                
                # 显示进度
                if quest.quest_type.value == "kill":
                    done = quest.targets.get("done", 0)
                    needed = quest.targets.get("count", 1)
                    print(f"   进度: {done}/{needed}")
                
                if quest.reward_gold > 0:
                    print(f"   奖励: {quest.reward_gold}金币, {quest.reward_exp}经验")
        
        if quests:
            print("\n【可接受的任务】")
            for i, quest in enumerate(quests, 1):
                print(f"\n{i}. {quest.title}")
                print(f"   描述: {quest.description}")
                print(f"   发布者: {quest.giver.name if quest.giver else '未知'}")
                if quest.reward_gold > 0:
                    print(f"   奖励: {quest.reward_gold}金币, {quest.reward_exp}经验")
        
        if not active_quests and not quests:
            print("\n当前没有任务。")
        
        self.wait_for_input()
    
    def show_npc_list(self, npcs: List[NPC]) -> Optional[NPC]:
        """
        显示NPC列表并选择
        
        Args:
            npcs: NPC列表
            
        Returns:
            选中的NPC（如果有效）
        """
        self.print_header("附近的NPC")
        
        if not npcs:
            print("\n附近没有NPC。")
            self.wait_for_input()
            return None
        
        options = []
        for i, npc in enumerate(npcs, 1):
            distance = 0  # 可以计算与玩家的距离
            status = "存活" if npc.is_alive else "已死亡"
            mood = npc.mood.value if hasattr(npc, 'mood') else "未知"
            
            options.append(MenuOption(
                str(i),
                f"{npc.name} ({npc.personality.profession}) - {status} - {mood}",
                lambda n=npc: n
            ))
        
        options.append(MenuOption("0", "返回", lambda: None))
        
        choice = self.get_user_choice(options)
        if choice:
            result = choice.action()
            if isinstance(result, NPC):
                return result
        
        return None
    
    def show_npc_dialog(self, npc: NPC, player: Player, openai_integration) -> str:
        """
        显示NPC对话界面
        
        Args:
            npc: NPC对象
            player: 玩家对象
            openai_integration: OpenAI集成对象
            
        Returns:
            选择的动作
        """
        self.print_header(f"与 {npc.name} 对话")
        
        print(f"\n{npc.name} ({npc.personality.profession})")
        print(f"情绪: {npc.mood.value if hasattr(npc, 'mood') else '未知'}")
        print(f"关系: {npc.relationship_with_player.value if hasattr(npc, 'relationship_with_player') else '未知'}")
        
        # 显示对话选项
        options = [
            MenuOption("1", "打招呼", lambda: "greet"),
            MenuOption("2", "询问任务", lambda: "ask_quest"),
            MenuOption("3", "查看任务", lambda: "view_quests"),
            MenuOption("4", "自由对话", lambda: "chat"),
            MenuOption("5", "交易", lambda: "trade"),
            MenuOption("0", "离开", lambda: "leave")
        ]
        
        choice = self.get_user_choice(options)
        if choice:
            action = choice.action()
            
            if action == "greet":
                message = "你好"
                response = openai_integration.generate_npc_response(npc, message)
                print(f"\n你说: {message}")
                print(f"{npc.name}: {response}")
                self.wait_for_input()
            
            elif action == "chat":
                message = input("\n你想说什么: ")
                if message:
                    response = openai_integration.generate_npc_response(npc, message)
                    print(f"\n你说: {message}")
                    print(f"{npc.name}: {response}")
                    self.wait_for_input()
            
            return action
        
        return "leave"
    
    def show_event_notification(self, event: GameEvent):
        """
        显示事件通知
        
        Args:
            event: 游戏事件
        """
        self.print_header("事件通知")
        print(f"\n{event.title}")
        print(f"\n{event.description}")
        
        if event.choices:
            print("\n选项:")
            for i, choice in enumerate(event.choices, 1):
                print(f"  {i}. {choice.get('text', '')}")
        
        self.wait_for_input()
    
    def show_colony_menu(self, resource_manager, building_manager):
        """
        显示基地管理菜单
        
        Args:
            resource_manager: 资源管理器
            building_manager: 建筑管理器
        """
        self.print_header("基地管理")
        
        print("\n【资源】")
        print(resource_manager)
        
        print("\n【建筑】")
        buildings = building_manager.buildings
        if buildings:
            for building in buildings:
                status = "完成" if building.is_completed else "建造中"
                print(f"  {building.building_type.value}: {status} (Lv.{building.level})")
        else:
            print("  暂无建筑")
        
        options = [
            MenuOption("1", "建造建筑", lambda: "build"),
            MenuOption("2", "查看生产", lambda: "production"),
            MenuOption("0", "返回", lambda: "back")
        ]
        
        choice = self.get_user_choice(options)
        if choice:
            return choice.action()
        
        return "back"
    
    def show_message(self, message: str):
        """
        显示消息
        
        Args:
            message: 消息文本
        """
        print(f"\n{message}")
        self.wait_for_input()


