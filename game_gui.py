"""
图形界面游戏主控制器
使用pygame实现的图形界面版本
"""

import sys
import os
import pygame
import time
import threading  # 添加线程模块用于异步处理

# 添加项目根目录到Python路径
_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

from core.game_engine import GameEngine
from core.world import Position, World
from core.locations import Location, LocationManager, LocationType
from entities.player import Player
from entities.npc import NPC, NPCPersonality, NPCRelationship
from colony.resource import ResourceManager, ResourceType
from colony.building import BuildingManager
from colony.production import ProductionSystem
from systems.quest import QuestManager
from systems.event import EventManager
from ui.game_window import GameWindow, GameView
from ai.openai_integration import get_openai_integration
from combat.weapons import get_weapon
from combat.combat_engine import CombatEngine
from utils.logger import get_logger
from utils.config import get_config
from typing import Optional, List


class GameGUI:
    """图形界面游戏主控制器"""
    
    def __init__(self):
        """初始化游戏"""
        self.logger = get_logger("GameGUI")
        self.config = get_config()
        
        # 初始化图形窗口
        self.window = GameWindow(width=1024, height=768)
        
        # 初始化核心系统
        self.engine = GameEngine(config_path="config.json")
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
        
        # 地点管理器
        self.location_manager = LocationManager()
        
        # 游戏状态
        self.running = False
        self.game_time = 0.0
        self.paused = False
        
        # 场景状态：'world_map' (大地图) 或 'local_map' (局部地图)
        self.current_scene = 'world_map'  # 默认在大地图
        self.current_location: Optional[Location] = None  # 当前所在的地点
        
        # 遭遇战冷却时间（防止重复触发导致卡死）
        self.encounter_cooldown = 0.0  # 冷却时间（秒）
        self._last_encounter_npc = None  # 上次遭遇的NPC（用于回退计算）
        self._last_move_delta = {'x': 0, 'y': 0}  # 上次移动增量（用于回退）
        
        # 输入状态
        self.keys_pressed = {}
        self.mouse_pos = (0, 0)
        self.mouse_clicked = False
        
        # UI状态
        self.current_view = GameView.WORLD
        self.menu_selected = 0
        self.dialog_npc: Optional[NPC] = None
        self.dialog_messages = []
        self.dialog_input = ""
        
        # 交易相关
        self.trade_npc: Optional[NPC] = None
        
        # 保存NPC AI引用
        self.npc_ais = {}
    
    def initialize_world(self):
        """初始化游戏世界（随机生成大地图）"""
        self.logger.info("初始化游戏世界（随机生成大地图）...")
        
        # === 创建更大的世界地图 ===
        world_width = 4000
        world_height = 3000
        self.engine.world = World(width=world_width, height=world_height, tile_size=32)
        self.logger.info(f"创建世界地图: {world_width}x{world_height}")
        
        # === 创建玩家（随机位置，确保不在水域） ===
        player_pos = self._find_valid_position(world_width, world_height, margin=200)
        self.player = Player(name="玩家", position=player_pos)
        self.engine.add_entity(self.player)
        self.logger.info(f"玩家初始位置: ({player_pos.x}, {player_pos.y})")
        
        # === 随机生成地点 ===
        self._generate_random_locations(world_width, world_height)
        
        # === 随机生成NPC军团（大地图上的军团） ===
        self.npcs = []
        self._generate_random_npc_armies(world_width, world_height)
        
        # 添加NPC到引擎并创建AI
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
        
        # 相机跟随玩家
        self.window.follow_entity(self.player)
        
        self.logger.info(f"游戏世界初始化完成 - 地点数: {len(self.location_manager.get_all_locations())}, NPC军团数: {len(self.npcs)}")
    
    def _find_valid_position(self, world_width: int, world_height: int, margin: int = 100) -> Position:
        """
        在世界上找到一个有效位置（不在水域）
        
        Args:
            world_width: 世界宽度
            world_height: 世界高度
            margin: 边界边距（避免太靠近边缘）
            
        Returns:
            有效的位置坐标
        """
        from core.world import TerrainType
        import random
        
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.uniform(margin, world_width - margin)
            y = random.uniform(margin, world_height - margin)
            pos = Position(x, y)
            
            # 检查地形是否为水域
            terrain = self.engine.world.get_global_terrain_at(pos)
            if terrain != TerrainType.WATER:
                return pos
        
        # 如果找不到，返回中心位置
        return Position(world_width // 2, world_height // 2)
    
    def _generate_random_locations(self, world_width: int, world_height: int):
        """随机生成大地图上的地点"""
        import random
        from core.world import TerrainType
        
        # 城镇名称池
        town_names = ["铁炉堡", "暴风城", "奥格瑞玛", "达拉然", "银月城", "雷霆崖", "幽暗城", "埃索达"]
        village_names = ["新手村", "宁静村", "丰收村", "橡木村", "石桥村", "溪水村", "阳光村", "绿野村", 
                        "牧羊村", "渔人村", "矿工村", "铁匠村", "商贾村", "学者村", "勇士村", "和平村"]
        resource_names = ["铁矿场", "金矿场", "木材场", "石料场", "渔场", "农场", "猎场", "采石场"]
        dungeon_names = ["暗影地牢", "废弃矿坑", "古墓", "恶魔巢穴", "亡灵洞窟", "龙穴", "遗迹", "迷宫"]
        
        locations = []
        
        # 生成城镇（3-5个）
        town_count = random.randint(3, 5)
        for i in range(town_count):
            pos = self._find_valid_position(world_width, world_height, margin=200)
            name = random.choice(town_names)
            town_names.remove(name) if name in town_names else None  # 避免重复
            
            location = Location(
                name=name,
                position=pos,
                location_type=LocationType.TOWN,
                faction=random.choice(["alliance", "neutral", "neutral"]),  # 大部分中立
                population=random.randint(300, 800)
            )
            locations.append(location)
        
        # 生成村庄（10-15个）
        village_count = random.randint(10, 15)
        for i in range(village_count):
            pos = self._find_valid_position(world_width, world_height, margin=150)
            name = random.choice(village_names)
            village_names.remove(name) if name in village_names else None
            
            location = Location(
                name=name,
                position=pos,
                location_type=LocationType.VILLAGE,
                faction="neutral",
                population=random.randint(50, 200)
            )
            locations.append(location)
        
        # 生成资源点（5-8个）
        resource_count = random.randint(5, 8)
        resource_types = ["iron", "gold", "wood", "stone", "food"]
        for i in range(resource_count):
            pos = self._find_valid_position(world_width, world_height, margin=100)
            name = random.choice(resource_names)
            resource_names.remove(name) if name in resource_names else None
            
            location = Location(
                name=name,
                position=pos,
                location_type=LocationType.RESOURCE_POINT,
                faction="neutral",
                resource_type=random.choice(resource_types),
                resource_amount=random.randint(500, 2000)
            )
            locations.append(location)
        
        # 添加到管理器
        for location in locations:
            self.location_manager.add_location(location)
        
        self.logger.info(f"随机生成了 {len(locations)} 个地点（{town_count}城镇, {village_count}村庄, {resource_count}资源点）")
    
    def _generate_random_npc_armies(self, world_width: int, world_height: int):
        """随机生成NPC军团（大地图上的军团）"""
        import random
        
        # 盗贼团名称池
        bandit_names = ["盗贼团", "黑帮", "土匪", "恶棍团伙", "掠夺者", "亡命之徒", "暗影帮", 
                       "血手帮", "狼群", "毒蛇团", "铁爪帮", "暗杀者", "劫匪", "恶人团", "暴徒"]
        merchant_names = ["商队A", "商队B", "旅行商人", "流动商贩", "商团", "贸易队", "商行", 
                         "商旅", "商贾团", "行商", "商帮", "商旅队"]
        patrol_names = ["巡逻队A", "巡逻队B", "守卫队", "边防军", "哨兵", "斥候队", "骑士团", 
                       "守备队", "卫队", "巡逻兵", "警戒队", "卫戍队"]
        
        # 生成盗贼团（10-15个）
        bandit_count = random.randint(10, 15)
        for i in range(bandit_count):
            pos = self._find_valid_position(world_width, world_height, margin=100)
            name = f"{random.choice(bandit_names)}{i+1}" if i > 0 else random.choice(bandit_names)
            
            npc = NPC(
                name=name,
                position=pos,
                personality=NPCPersonality(
                    traits=["aggressive", "cruel"],
                    aggression=random.randint(70, 95),
                    profession="bandit"
                )
            )
            npc.faction = "bandit"
            npc.is_world_entity = True  # 标记为大地图实体
            self.npcs.append(npc)
        
        # 生成商队（5-8个）
        merchant_count = random.randint(5, 8)
        for i in range(merchant_count):
            pos = self._find_valid_position(world_width, world_height, margin=100)
            name = f"{random.choice(merchant_names)}{i+1}" if i > 0 else random.choice(merchant_names)
            
            npc = NPC(
                name=name,
                position=pos,
                personality=NPCPersonality(
                    traits=["greedy", "clever"],
                    kindness=random.randint(30, 60),
                    profession="merchant"
                )
            )
            npc.faction = "neutral"
            npc.is_world_entity = True  # 标记为大地图实体
            self.npcs.append(npc)
        
        # 生成巡逻队（5-8个）
        patrol_count = random.randint(5, 8)
        for i in range(patrol_count):
            pos = self._find_valid_position(world_width, world_height, margin=100)
            name = f"{random.choice(patrol_names)}{i+1}" if i > 0 else random.choice(patrol_names)
            
            npc = NPC(
                name=name,
                position=pos,
                personality=NPCPersonality(
                    traits=["brave", "loyal"],
                    aggression=random.randint(40, 70),
                    loyalty=random.randint(70, 95),
                    profession="soldier"
                )
            )
            npc.faction = "alliance"
            npc.is_world_entity = True  # 标记为大地图实体
            self.npcs.append(npc)
        
        self.logger.info(f"随机生成了 {len(self.npcs)} 个NPC军团（{bandit_count}盗贼团, {merchant_count}商队, {patrol_count}巡逻队）")
    
    def _create_initial_quests(self):
        """创建初始任务（随机生成模式下，任务将由村庄NPC提供）"""
        # 在随机生成模式下，初始任务可以从第一个村庄获取
        # 这里暂时不创建任务，等玩家进入村庄后再生成任务
        # 或者可以从location_manager的第一个村庄创建任务
        locations = self.location_manager.get_all_locations()
        village_locations = [loc for loc in locations if loc.location_type == LocationType.VILLAGE]
        
        if len(village_locations) > 0:
            # 可以在这里为第一个村庄创建初始任务
            # 但为了简化，暂时不创建，等玩家进入村庄时再生成
            self.logger.debug(f"找到 {len(village_locations)} 个村庄，可以后续生成任务")
    
    def start(self):
        """启动游戏"""
        self.logger.info("=" * 50)
        self.logger.info("骑砍环世界融合游戏（图形界面版）启动")
        self.logger.info("=" * 50)
        
        # 初始化世界
        self.initialize_world()
        
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
            
            if not self.paused:
                self.game_time += delta_time
                # 更新游戏系统
                self.update_game_systems(delta_time)
                # 处理输入（移动需要delta_time）
                self.handle_input(delta_time)
            else:
                # 暂停时仍然处理输入（菜单操作）
                self.handle_input(0.0)
            
            # 渲染
            self.render()
            
            # 检查游戏结束条件
            if not self.player.is_alive:
                self.show_game_over()
                break
    
    def update_game_systems(self, delta_time: float):
        """更新游戏系统"""
        # === 🔴 修复：如果处于对话、菜单、交易或战利品界面，暂停游戏世界的更新 ===
        # 防止在对话时被其他 NPC 攻击，避免逻辑冲突
        if self.current_view in [GameView.DIALOG, GameView.MENU, GameView.TRADE]:
            # 注意：如果以后添加了 GameView.LOOT，请在这里添加
            return
        
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
        
        # === 🔴 紧急修复：更新遭遇战冷却时间，防止重复触发导致卡死 ===
        if self.encounter_cooldown > 0.0:
            self.encounter_cooldown -= delta_time
            if self.encounter_cooldown < 0.0:
                self.encounter_cooldown = 0.0
        
        # 更新战斗提示消息计时器
        if hasattr(self, '_combat_message_timer'):
            self._combat_message_timer -= delta_time
            if self._combat_message_timer <= 0:
                # 清除过期的战斗消息
                if hasattr(self, '_combat_message'):
                    delattr(self, '_combat_message')
                delattr(self, '_combat_message_timer')
        
        # 检查战斗是否结束（敌人或玩家死亡）
        if self.current_scene == 'local_map' and hasattr(self, '_combat_enemy'):
            enemy = self._combat_enemy
            if not enemy.is_alive or not self.player.is_alive:
                # 战斗结束，延迟返回大地图（给玩家看到结果的时间）
                if not hasattr(self, '_combat_end_timer'):
                    self._combat_end_timer = 2.0  # 2秒后返回大地图
                else:
                    self._combat_end_timer -= delta_time
                    if self._combat_end_timer <= 0:
                        self.exit_combat_encounter()
                        if hasattr(self, '_combat_end_timer'):
                            delattr(self, '_combat_end_timer')
        
        # 相机跟随玩家
        self.window.follow_entity(self.player)
    
    def handle_input(self, delta_time: float = 0.0):
        """处理输入"""
        # 获取按键状态
        self.keys_pressed = pygame.key.get_pressed()
        
        # 处理玩家移动（WASD或方向键）
        if not self.paused and self.current_view == GameView.WORLD and delta_time > 0:
            move_speed = self.player.current_speed  # 使用角色的实际移动速度
            
            # 在大地图模式下，移动速度更快（模拟军团移动）
            if self.current_scene == 'world_map':
                move_speed *= 3.0  # 大地图移动速度是局部地图的3倍
            
            move_x, move_y = 0, 0
            
            if self.keys_pressed[pygame.K_w] or self.keys_pressed[pygame.K_UP]:
                move_y -= move_speed * delta_time
            if self.keys_pressed[pygame.K_s] or self.keys_pressed[pygame.K_DOWN]:
                move_y += move_speed * delta_time
            if self.keys_pressed[pygame.K_a] or self.keys_pressed[pygame.K_LEFT]:
                move_x -= move_speed * delta_time
            if self.keys_pressed[pygame.K_d] or self.keys_pressed[pygame.K_RIGHT]:
                move_x += move_speed * delta_time
            
            # === 🔴 修复：分离轴移动 (Axis Separation)，解决移动卡顿与粘滞 ===
            # 先处理 X 轴移动
            if move_x != 0:
                # 保存原始X位置
                old_x = self.player.position.x
                
                # 尝试更新 X 坐标
                self.player.position.x += move_x
                
                # X 轴边界检查
                self.player.position.x = max(0, min(self.engine.world.width, self.player.position.x))
                
                # 碰撞检测（仅在局部地图有效）
                if self.current_scene == 'local_map' and not self.engine.world.can_move_to(self.player.position):
                    # 如果撞墙，只回退 X，保留 Y 轴的移动可能性
                    self.player.position.x = old_x
            
            # 后处理 Y 轴移动（基于已经更新后的 X）
            if move_y != 0:
                # 保存原始Y位置
                old_y = self.player.position.y
                
                # 尝试更新 Y 坐标
                self.player.position.y += move_y
                
                # Y 轴边界检查
                self.player.position.y = max(0, min(self.engine.world.height, self.player.position.y))
                
                # 碰撞检测
                if self.current_scene == 'local_map' and not self.engine.world.can_move_to(self.player.position):
                    # 如果撞墙，只回退 Y
                    self.player.position.y = old_y
        
        # === 大地图碰撞检测：检查是否与NPC军团接触 ===
        # 注意：冷却检查已经在 _check_npc_encounters 方法内部进行，这里只检查基本条件
        if (self.current_scene == 'world_map' and 
            self.player and 
            not self.paused):
            self._check_npc_encounters()  # 冷却和反弹逻辑都在方法内部处理
        
        # 处理事件
        events = self.window.handle_events()
        if events is None:  # 退出事件
            self.running = False
            return
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos
    
    def handle_keydown(self, key):
        """处理按键按下"""
        if key == pygame.K_m:  # 菜单
            if self.current_view == GameView.WORLD:
                self.current_view = GameView.MENU
                self.menu_selected = 0
            else:
                self.current_view = GameView.WORLD
                
        elif key == pygame.K_TAB:  # TAB键：在大地图和局部地图之间切换
            if self.current_scene == 'world_map':
                # 检查是否在地点附近，如果是则可以进入
                nearby_location = self.location_manager.get_location_at(
                    self.player.position, 
                    radius=100.0
                )
                if nearby_location and nearby_location.is_enterable():
                    self.enter_location(nearby_location)
            elif self.current_scene == 'local_map':
                # 离开局部地图，返回大地图（支持战斗遭遇和地点）
                self.exit_location()
        
        elif key == pygame.K_f:  # F键：在大地图模式下进入地点
            if self.current_scene == 'world_map':
                nearby_location = self.location_manager.get_location_at(
                    self.player.position, 
                    radius=100.0
                )
                if nearby_location and nearby_location.is_enterable():
                    self.enter_location(nearby_location)
        
        elif key == pygame.K_i:  # 背包
            if self.current_view == GameView.WORLD:
                self.current_view = GameView.INVENTORY
            else:
                self.current_view = GameView.WORLD
        
        elif key == pygame.K_q:  # 任务
            if self.current_view == GameView.WORLD:
                self.current_view = GameView.QUEST
            else:
                self.current_view = GameView.WORLD
        
        elif key == pygame.K_c:  # 基地
            if self.current_view == GameView.WORLD:
                self.current_view = GameView.COLONY
            else:
                self.current_view = GameView.WORLD
        
        elif key == pygame.K_ESCAPE:  # ESC返回
            if self.current_view == GameView.TRADE:
                # 离开交易界面
                self.logger.debug("ESC键：离开交易界面")
                # 先保存NPC引用，再清除
                trade_npc = self.trade_npc
                self.current_view = GameView.WORLD
                self.trade_npc = None
                # 推开玩家，防止卡死
                if trade_npc:
                    self._push_player_away_from_npc(trade_npc, distance=40.0)
            elif self.current_view != GameView.WORLD:
                self.current_view = GameView.WORLD
                self.dialog_npc = None
            else:
                self.paused = not self.paused
        
        elif key == pygame.K_m and pygame.KMOD_SHIFT:  # Shift+M 切换小地图（避免冲突）
            self.window.minimap.toggle()
        
        elif key == pygame.K_RETURN:  # 回车
            if self.current_view == GameView.MENU:
                self.handle_menu_select()
            elif self.current_view == GameView.DIALOG:
                # 检查是否是NPC遭遇对话框
                if hasattr(self, '_npc_encounter_choice_pending') and self._npc_encounter_choice_pending:
                    # 处理遭遇选择（需要输入数字键）
                    pass
                else:
                    self.handle_dialog_send()
        
        # 处理NPC遭遇对话框的选择（数字键1-3）
        elif key in [pygame.K_1, pygame.K_2, pygame.K_3]:
            if (hasattr(self, '_npc_encounter_choice_pending') and 
                self._npc_encounter_choice_pending and 
                self.current_view == GameView.DIALOG and 
                self.dialog_npc):
                
                choice = key - pygame.K_0  # 获取数字1-3
                self.handle_npc_encounter_choice(choice)
        
        # === 🔴 修复：处理交易界面的数字键（1-8）购买/出售 ===
        elif key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8]:
            if self.current_view == GameView.TRADE and self.trade_npc:
                # 调试日志
                self.logger.debug(f"交易界面按键检测：按下了键 {key}, 当前视图: {self.current_view}")
                item_index = key - pygame.K_0  # 获取数字1-8
                # 检查是否按下了Shift键（出售）或普通数字键（购买）
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                    # Shift+数字键：出售玩家物品
                    self.logger.debug(f"检测到Shift+{item_index}，执行出售操作")
                    self._handle_trade_sell_item(item_index)
                else:
                    # 数字键：购买商人物品
                    self.logger.debug(f"检测到数字键{item_index}，执行购买操作")
                    self._handle_trade_buy_item(item_index)
            elif self.current_view == GameView.TRADE:
                # 如果处于交易界面但trade_npc为None，记录警告
                self.logger.warning(f"交易界面按键检测：当前在交易界面但trade_npc为None")
        
        elif key == pygame.K_UP:
            if self.current_view == GameView.MENU:
                self.menu_selected = max(0, self.menu_selected - 1)
        
        elif key == pygame.K_DOWN:
            if self.current_view == GameView.MENU:
                menu_items = self.get_menu_items()
                self.menu_selected = min(len(menu_items) - 1, self.menu_selected + 1)
        
        elif key == pygame.K_BACKSPACE:
            if self.current_view == GameView.DIALOG:
                self.dialog_input = self.dialog_input[:-1]
        
        else:
            # 处理文本输入
            if self.current_view == GameView.DIALOG and 32 <= key <= 126:
                char = chr(key)
                self.dialog_input += char
    
    def handle_mouse_click(self, pos):
        """处理鼠标点击"""
        # 在世界视图中点击NPC
        if self.current_view == GameView.WORLD:
            world_pos = self.window.screen_to_world(pos[0], pos[1])
            
            # 检查是否点击了NPC
            for npc in self.npcs:
                if npc.position.distance_to(world_pos) < 50:
                    self.dialog_npc = npc
                    self.current_view = GameView.DIALOG
                    self.dialog_messages = []
                    self.dialog_input = ""
                    break
    
    def get_menu_items(self) -> List[tuple]:
        """获取菜单项"""
        return [
            ("1", "继续游戏"),
            ("2", "查看状态"),
            ("3", "保存游戏"),
            ("4", "退出游戏")
        ]
    
    def handle_menu_select(self):
        """处理菜单选择"""
        menu_items = self.get_menu_items()
        if self.menu_selected < len(menu_items):
            key, text = menu_items[self.menu_selected]
            
            if key == "1":
                self.current_view = GameView.WORLD
            elif key == "2":
                # 显示状态（简化处理）
                self.current_view = GameView.WORLD
            elif key == "4":
                self.running = False
    
    def handle_dialog_send(self):
        """处理对话发送（使用异步线程避免卡顿）"""
        if self.dialog_npc and self.dialog_input.strip():
            message = self.dialog_input.strip()
            self.dialog_messages.append(f"你: {message}")
            
            # 清空输入框
            self.dialog_input = ""
            
            # 显示正在输入状态
            self.dialog_messages.append(f"{self.dialog_npc.name}: (正在思考...)")
            
            # 启动新线程处理网络请求，避免卡死主界面
            threading.Thread(
                target=self._async_npc_response,
                args=(self.dialog_npc, message),
                daemon=True
            ).start()
    
    def _async_npc_response(self, npc, message):
        """异步获取NPC回复（在独立线程中运行）"""
        try:
            response = self.openai.generate_npc_response(npc, message)
            
            # 移除"(正在思考...)"并添加真实回复
            # 使用线程锁保证线程安全
            if hasattr(self, '_dialog_lock'):
                with self._dialog_lock:
                    if self.dialog_messages and "(正在思考...)" in self.dialog_messages[-1]:
                        self.dialog_messages.pop()
                    self.dialog_messages.append(f"{npc.name}: {response}")
            else:
                # 如果没有锁，简单处理（Python的GIL让list操作相对安全）
                if self.dialog_messages and "(正在思考...)" in self.dialog_messages[-1]:
                    self.dialog_messages.pop()
                self.dialog_messages.append(f"{npc.name}: {response}")
        except Exception as e:
            # 错误处理
            if self.dialog_messages and "(正在思考...)" in self.dialog_messages[-1]:
                self.dialog_messages.pop()
            self.dialog_messages.append(f"{npc.name}: (抱歉，我无法理解...)")
            self.logger.error(f"NPC回复生成失败: {e}")
    
    def _check_npc_encounters(self) -> bool:
        """
        检查玩家与NPC军团的碰撞（大地图模式）
        如果与敌对NPC接触，触发遭遇战
        
        Returns:
            bool: 是否触发了遭遇（True表示已触发，False表示未触发）
        """
        # === 🔴 紧急修复：首先检查冷却时间，防止重复触发导致卡死 ===
        if self.encounter_cooldown > 0.0:
            return False
        
        if not self.player or self.current_scene != 'world_map':
            return False
        
        encounter_radius = 20.0  # 碰撞检测半径（像素）
        encounter_radius_sq = encounter_radius ** 2  # 使用平方距离避免开方
        
        for npc in self.npcs:
            # === 修复：只检查大地图实体（避免检查局部地图NPC） ===
            if not getattr(npc, 'is_world_entity', True):
                continue
            
            if not hasattr(npc, 'is_alive') or not npc.is_alive:
                continue
            
            # 计算距离（使用平方距离优化性能）
            dx = self.player.position.x - npc.position.x
            dy = self.player.position.y - npc.position.y
            dist_sq = dx ** 2 + dy ** 2
            
            if dist_sq <= encounter_radius_sq:
                # === 🔴 紧急修复：立即设置冷却时间，防止重复触发 ===
                self.encounter_cooldown = 3.0  # 3秒冷却时间
                
                # === 🔴 紧急修复：无论敌对还是中立，都执行反弹逻辑（推开30像素） ===
                distance = dist_sq ** 0.5  # 计算实际距离
                if distance > 0:
                    # 计算从NPC指向玩家的方向（推开方向）
                    push_x = (dx / distance) * 30.0  # 推开30像素（增大推开距离）
                    push_y = (dy / distance) * 30.0
                    
                    # 应用推开效果
                    self.player.position.x += push_x
                    self.player.position.y += push_y
                    
                    # 边界检查，确保不超出世界范围
                    self.player.position.x = max(0, min(self.engine.world.width, self.player.position.x))
                    self.player.position.y = max(0, min(self.engine.world.height, self.player.position.y))
                    
                    self.logger.debug(f"玩家被推开: ({push_x:.1f}, {push_y:.1f})")
                
                # 检查NPC的势力关系
                npc_faction = getattr(npc, 'faction', 'neutral')
                
                # 保存遭遇的NPC
                self._last_encounter_npc = npc
                
                # 敌对势力：自动触发战斗
                if npc_faction in ['enemy', 'bandit']:
                    self.logger.info(f"遭遇敌对军团: {npc.name} ({npc_faction})")
                    self.enter_combat_encounter(npc)
                    return True  # 返回True表示已触发遭遇
                
                # 中立/友善势力：显示交互选项
                elif npc_faction in ['neutral', 'alliance']:
                    # === 修复：移除 _encounter_triggered 检查，允许重复交互 ===
                    # 只要过了冷却时间并再次接触，就可以再次触发对话
                    self.show_npc_encounter_dialog(npc)
                    return True  # 返回True表示已触发遭遇
        
        return False  # 未触发任何遭遇
    
    def enter_combat_encounter(self, enemy_npc: NPC):
        """
        进入战斗遭遇（从大地图切换到战斗场景）
        
        Args:
            enemy_npc: 遭遇的敌人NPC
        """
        if not enemy_npc or not self.player:
            return
        
        self.logger.info(f"进入战斗遭遇：玩家 vs {enemy_npc.name}")
        
        # 生成战斗地图
        battlefield = self._generate_battlefield()
        
        # 保存战斗前的状态
        self._pre_combat_world = self.engine.world
        self._pre_combat_player_pos = Position(self.player.position.x, self.player.position.y)
        self._combat_enemy = enemy_npc
        
        # 保存敌人的战斗前位置（用于战斗后恢复或移除）
        if not hasattr(enemy_npc, '_pre_combat_pos'):
            enemy_npc._pre_combat_pos = Position(enemy_npc.position.x, enemy_npc.position.y)
        
        # 切换到战斗场景
        self.current_scene = 'local_map'
        self.engine.world = battlefield
        
        # 设置玩家和敌人的位置（地图两端）
        self.player.position.x = 100
        self.player.position.y = battlefield.height - 100
        
        # 设置敌人位置
        enemy_npc.position.x = battlefield.width - 100
        enemy_npc.position.y = 100
        
        # 将敌人添加到战斗场景的实体列表（如果还没有）
        if enemy_npc not in self.engine.entities:
            self.engine.add_entity(enemy_npc)
        
        # 让敌人的AI进入战斗状态
        if enemy_npc in self.npc_ais:
            self.npc_ais[enemy_npc].start_combat(self.player)
        
        # 设置相机位置（战斗场景中心）
        self.window.camera_x = battlefield.width // 2
        self.window.camera_y = battlefield.height // 2
        
        # 显示战斗提示（可以通过UI显示）
        self._combat_message = f"遭遇敌军！{enemy_npc.name} - 战斗开始！"
        self._combat_message_timer = 3.0  # 显示3秒
        
        self.logger.info(self._combat_message)
    
    def _generate_battlefield(self) -> 'World':
        """
        生成战斗地图（战场）
        
        Returns:
            World对象，代表战场
        """
        from core.world import TerrainType
        
        # 创建中等大小的战斗地图
        battlefield = World(width=1500, height=1500, tile_size=32)
        
        # 简化地形生成：主要是草地，少量障碍物
        grid_width = battlefield.width // battlefield.tile_size
        grid_height = battlefield.height // battlefield.tile_size
        
        # 重置为草地
        battlefield.terrain_grid = [
            [TerrainType.GRASS for _ in range(grid_width)]
            for _ in range(grid_height)
        ]
        
        # 添加一些森林作为障碍物（10%的区域）
        import random
        obstacle_count = (grid_width * grid_height) // 10
        
        for _ in range(obstacle_count):
            x = random.randint(0, grid_width - 1)
            y = random.randint(0, grid_height - 1)
            # 避免在起始位置附近放置障碍物
            if not (x < 5 and y > grid_height - 5) and not (x > grid_width - 5 and y < 5):
                battlefield.terrain_grid[y][x] = TerrainType.FOREST
        
        return battlefield
    
    def exit_combat_encounter(self):
        """退出战斗遭遇（返回大地图）"""
        if self.current_scene != 'local_map' or not hasattr(self, '_pre_combat_world'):
            return
        
        self.logger.info("战斗结束，返回大地图")
        
        # 恢复战斗前的世界
        if hasattr(self, '_pre_combat_world'):
            self.engine.world = self._pre_combat_world
        
        # 恢复玩家位置
        if hasattr(self, '_pre_combat_player_pos'):
            self.player.position.x = self._pre_combat_player_pos.x
            self.player.position.y = self._pre_combat_player_pos.y
        
        # 清理战斗状态
        if hasattr(self, '_combat_enemy'):
            enemy = self._combat_enemy
            # 如果敌人已死亡，从世界中移除
            if not enemy.is_alive and enemy in self.engine.entities:
                self.engine.remove_entity(enemy)
            # 如果敌人还活着，恢复其在大地图的位置（可选）
            elif enemy.is_alive and hasattr(enemy, '_pre_combat_pos'):
                enemy.position.x = enemy._pre_combat_pos.x
                enemy.position.y = enemy._pre_combat_pos.y
        
        # 切换回大地图
        self.current_scene = 'world_map'
        self.current_location = None
        
        # 清理战斗相关属性
        if hasattr(self, '_pre_combat_world'):
            delattr(self, '_pre_combat_world')
        if hasattr(self, '_pre_combat_player_pos'):
            delattr(self, '_pre_combat_player_pos')
        if hasattr(self, '_combat_enemy'):
            delattr(self, '_combat_enemy')
        if hasattr(self, '_combat_message'):
            delattr(self, '_combat_message')
        if hasattr(self, '_combat_message_timer'):
            delattr(self, '_combat_message_timer')
        
        # 恢复相机跟随玩家
        if self.player:
            self.window.follow_entity(self.player)
    
    def show_npc_encounter_dialog(self, npc: NPC):
        """
        显示NPC遭遇对话框（中立/友善NPC）
        
        Args:
            npc: 遭遇的NPC
        """
        self.logger.info(f"遭遇中立NPC: {npc.name}")
        
        # 设置对话框状态
        self.dialog_npc = npc
        self.current_view = GameView.DIALOG
        self.dialog_messages = [
            f"{npc.name}: 你好，旅者。",
            "你可以选择：",
            "[1] 交谈",
            "[2] 交易",
            "[3] 攻击",
            "按对应数字键选择，按ESC取消"
        ]
        self.dialog_input = ""
        
        # 标记：等待用户选择
        self._npc_encounter_choice_pending = True
    
    def enter_location(self, location: Location):
        """
        进入地点（从大地图切换到局部地图）
        
        Args:
            location: 要进入的地点
        """
        if not location or not location.is_enterable():
            return
        
        self.logger.info(f"进入地点: {location.name}")
        
        # === 🔴 修复：保存大地图引用和玩家坐标 ===
        # 保存当前大地图引用
        self._world_map_ref = self.engine.world
        
        # 保存玩家当前在大地图上的坐标
        self._pre_location_pos = Position(self.player.position.x, self.player.position.y)
        
        # 获取或生成局部地图
        scene_data = location.enter()
        local_map = scene_data.get('local_map') or location.local_map
        
        if not local_map:
            self.logger.error(f"地点 {location.name} 没有局部地图")
            return
        
        # === 🔴 修复：更新引擎的世界引用为局部地图 ===
        self.engine.world = local_map
        self.current_location = location
        self.current_scene = 'local_map'
        
        # === 🔴 修复：寻找安全位置，避免出生在障碍物上 ===
        # 使用循环寻找安全位置（不在障碍物上）
        import random
        safe_pos = None
        start_x = 100.0
        start_y = local_map.height - 100.0
        max_attempts = 50  # 最多尝试50次
        
        for attempt in range(max_attempts):
            # 尝试位置（第一次使用初始位置，之后随机偏移）
            if attempt == 0:
                test_x = start_x
                test_y = start_y
            else:
                # 随机偏移
                test_x = start_x + random.uniform(-200, 200)
                test_y = start_y + random.uniform(-200, 200)
            
            # 边界检查
            test_x = max(50, min(local_map.width - 50, test_x))
            test_y = max(50, min(local_map.height - 50, test_y))
            
            # 检查是否可以移动到该位置
            test_pos = Position(test_x, test_y)
            if local_map.can_move_to(test_pos):
                safe_pos = test_pos
                break
        
        # 如果找到了安全位置，使用它；否则使用初始位置（即使可能卡住）
        if safe_pos:
            self.player.position.x = safe_pos.x
            self.player.position.y = safe_pos.y
            self.logger.debug(f"找到安全位置: ({safe_pos.x:.1f}, {safe_pos.y:.1f})")
        else:
            # 保底：使用初始位置
            self.player.position.x = start_x
            self.player.position.y = start_y
            self.logger.warning(f"未找到安全位置，使用初始位置: ({start_x:.1f}, {start_y:.1f})")
        
        # 最终边界检查
        self.player.position.x = max(0, min(local_map.width, self.player.position.x))
        self.player.position.y = max(0, min(local_map.height, self.player.position.y))
        
        # === 🔴 修复：加载本地NPC到引擎 ===
        local_npcs = scene_data.get('npcs', [])
        if local_npcs:
            self.logger.info(f"加载 {len(local_npcs)} 个本地NPC到引擎")
            for npc in local_npcs:
                # === 🔴 修复：强制设置 is_world_entity = False，防止NPC鬼影问题 ===
                npc.is_world_entity = False  # 标记为本地实体，防止出现在大地图上
                # 添加到引擎实体列表
                self.engine.add_entity(npc)
                # 初始化NPC AI
                from ai.npc_ai import NPCAI
                self.npc_ais[npc] = NPCAI(npc, combat_engine=self.combat_engine)
        
        # 设置相机位置（局部地图中心）
        self.window.camera_x = local_map.width // 2
        self.window.camera_y = local_map.height // 2
        
        self.logger.info(f"已切换到局部地图，玩家位置重置为 ({self.player.position.x}, {self.player.position.y})")
    
    def handle_npc_encounter_choice(self, choice: int):
        """
        处理NPC遭遇对话框的选择
        
        Args:
            choice: 选择（1=交谈，2=交易，3=攻击）
        """
        if not self.dialog_npc:
            return
        
        npc = self.dialog_npc
        
        # 清除选择状态
        if hasattr(self, '_npc_encounter_choice_pending'):
            self._npc_encounter_choice_pending = False
        
        if choice == 1:  # 交谈
            self.logger.info(f"与 {npc.name} 开始对话")
            # 切换到正常对话模式
            self.dialog_messages = [f"{npc.name}: 你好，有什么可以帮助你的吗？"]
            self.dialog_input = ""
            
            # === 🔴 修复：强制执行推开逻辑，防止对话结束后卡死 ===
            # 推开距离必须大于检测半径(20.0)，使用40.0确保彻底脱离触发圈
            self._push_player_away_from_npc(npc, distance=40.0)
        
        elif choice == 2:  # 交易
            self.logger.info(f"与 {npc.name} 开始交易")
            # 切换到交易界面
            self.current_view = GameView.TRADE
            self.trade_npc = npc
            self.dialog_npc = None  # 清除对话NPC
            
            # === 🔴 修复：强制执行推开逻辑，防止交易结束后卡死 ===
            # 推开距离必须大于检测半径(20.0)，使用40.0确保彻底脱离触发圈
            self._push_player_away_from_npc(npc, distance=40.0)
            
            # 如果商人背包为空，生成一些默认商品
            if not hasattr(npc, 'inventory') or not npc.inventory:
                npc.inventory = {
                    "铁剑": {"count": 1, "price": 100},
                    "皮甲": {"count": 1, "price": 80},
                    "治疗药水": {"count": 3, "price": 20},
                    "面包": {"count": 10, "price": 2},
                    "箭矢": {"count": 50, "price": 1},
                }
                # 给商人一些金币
                if not hasattr(npc, 'money'):
                    npc.money = 500
            
            # 确保玩家有背包（如果为空，初始化一些物品）
            if not hasattr(self.player, 'inventory') or not self.player.inventory:
                self.player.inventory = {
                    "木材": {"count": 10, "price": 5},
                    "石头": {"count": 5, "price": 8},
                }
        
        elif choice == 3:  # 攻击
            self.logger.info(f"玩家选择攻击 {npc.name}")
            # 切换NPC为敌对，触发战斗
            npc.faction = "enemy"
            npc.relationship_with_player = NPCRelationship.HOSTILE
            self.current_view = GameView.WORLD
            self.dialog_npc = None
            # 立即触发战斗
            self.enter_combat_encounter(npc)
    
    def _handle_trade_buy_item(self, item_index: int):
        """
        处理交易界面的购买操作
        
        Args:
            item_index: 物品索引（1-8）
        """
        if not self.trade_npc:
            return
        
        # 获取商人的物品列表
        merchant_items = getattr(self.trade_npc, 'inventory', {})
        if not merchant_items:
            self.logger.warning("商人没有物品")
            return
        
        # 将字典转换为列表（按顺序）
        merchant_item_list = list(merchant_items.items())
        
        # 检查索引是否有效（1-8，对应索引0-7）
        if item_index < 1 or item_index > len(merchant_item_list):
            self.logger.warning(f"无效的物品索引: {item_index}")
            return
        
        # 获取选中的物品
        item_name, item_data = merchant_item_list[item_index - 1]
        item_price = item_data.get('price', 0)
        item_count = item_data.get('count', 0)
        
        if item_count <= 0:
            self.logger.warning(f"{item_name} 已售罄")
            return
        
        # === 实现买入逻辑 ===
        player_money = getattr(self.player, 'money', 0)
        
        if player_money < item_price:
            self.logger.warning(f"金币不足！需要 {item_price} 金币，但只有 {player_money} 金币")
            return
        
        # 执行交易
        # 1. 玩家扣钱
        self.player.money -= item_price
        
        # 2. 玩家加物品
        if not hasattr(self.player, 'inventory'):
            self.player.inventory = {}
        
        if item_name in self.player.inventory:
            self.player.inventory[item_name]['count'] += 1
        else:
            self.player.inventory[item_name] = {'count': 1, 'price': item_price}
        
        # 3. 商人减物品
        item_data['count'] -= 1
        if item_data['count'] <= 0:
            # 如果数量为0，从字典中移除
            del merchant_items[item_name]
        
        # 4. 商人加钱
        if not hasattr(self.trade_npc, 'money'):
            self.trade_npc.money = 0
        self.trade_npc.money += item_price
        
        self.logger.info(f"购买成功：{item_name} (花费 {item_price} 金币)")
    
    def _handle_trade_sell_item(self, item_index: int):
        """
        处理交易界面的出售操作
        
        Args:
            item_index: 物品索引（1-8）
        """
        if not self.trade_npc:
            return
        
        # 获取玩家的物品列表
        player_items = getattr(self.player, 'inventory', {})
        if not player_items:
            self.logger.warning("你的背包为空")
            return
        
        # 将字典转换为列表（按顺序）
        player_item_list = list(player_items.items())
        
        # 检查索引是否有效（1-8，对应索引0-7）
        if item_index < 1 or item_index > len(player_item_list):
            self.logger.warning(f"无效的物品索引: {item_index}")
            return
        
        # 获取选中的物品
        item_name, item_data = player_item_list[item_index - 1]
        item_price = item_data.get('price', 0)
        item_count = item_data.get('count', 0)
        
        if item_count <= 0:
            self.logger.warning(f"{item_name} 数量不足")
            return
        
        # 计算出售价格（通常是购买价格的70%）
        sell_price = int(item_price * 0.7) if item_price > 0 else 0
        
        # 检查商人是否有足够的金币
        merchant_money = getattr(self.trade_npc, 'money', 0)
        if merchant_money < sell_price:
            self.logger.warning(f"商人金币不足！需要 {sell_price} 金币，但商人只有 {merchant_money} 金币")
            return
        
        # 执行交易
        # 1. 玩家加钱
        self.player.money += sell_price
        
        # 2. 玩家减物品
        item_data['count'] -= 1
        if item_data['count'] <= 0:
            # 如果数量为0，从字典中移除
            del player_items[item_name]
        
        # 3. 商人加物品
        if not hasattr(self.trade_npc, 'inventory'):
            self.trade_npc.inventory = {}
        
        merchant_items = self.trade_npc.inventory
        if item_name in merchant_items:
            merchant_items[item_name]['count'] += 1
        else:
            merchant_items[item_name] = {'count': 1, 'price': item_price}
        
        # 4. 商人扣钱
        if not hasattr(self.trade_npc, 'money'):
            self.trade_npc.money = 0
        self.trade_npc.money -= sell_price
        
        self.logger.info(f"出售成功：{item_name} (获得 {sell_price} 金币)")
    
    def _push_player_away_from_npc(self, npc: NPC, distance: float = 20.0):
        """
        将玩家推开，远离NPC（防止位置重叠导致卡死）
        
        Args:
            npc: NPC对象
            distance: 推开距离（像素）
        """
        if not self.player or not npc:
            return
        
        # 计算从NPC指向玩家的方向
        dx = self.player.position.x - npc.position.x
        dy = self.player.position.y - npc.position.y
        dist_sq = dx ** 2 + dy ** 2
        
        if dist_sq > 0:
            # 计算实际距离
            dist = dist_sq ** 0.5
            
            # 如果距离太近，推开玩家
            if dist < distance * 2:
                # 计算推开方向（从NPC指向玩家）
                push_x = (dx / dist) * distance
                push_y = (dy / dist) * distance
                
                # 应用推开效果
                self.player.position.x += push_x
                self.player.position.y += push_y
                
                # 边界检查
                if hasattr(self.engine, 'world') and self.engine.world:
                    self.player.position.x = max(0, min(self.engine.world.width, self.player.position.x))
                    self.player.position.y = max(0, min(self.engine.world.height, self.player.position.y))
                
                self.logger.debug(f"推开玩家远离 {npc.name}: ({push_x:.1f}, {push_y:.1f})")
    
    def exit_location(self):
        """离开地点（从局部地图切换回大地图）"""
        if self.current_scene != 'local_map':
            return
        
        # 检查是否是战斗遭遇
        if hasattr(self, '_combat_enemy'):
            self.exit_combat_encounter()
            return
        
        # 正常离开地点
        location_name = self.current_location.name if self.current_location else '未知'
        self.logger.info(f"离开地点: {location_name}")
        
        # === 🔴 修复：清理本地NPC（从引擎移除，但保留在Location对象中） ===
        local_npcs_to_remove = []
        for entity in list(self.engine.entities):
            if isinstance(entity, NPC) and not getattr(entity, 'is_world_entity', True):
                # 这是局部地图NPC，需要移除
                local_npcs_to_remove.append(entity)
                self.engine.remove_entity(entity)
                # 清理对应的AI
                if entity in self.npc_ais:
                    del self.npc_ais[entity]
        
        if local_npcs_to_remove:
            self.logger.info(f"清理了 {len(local_npcs_to_remove)} 个本地NPC")
        
        # === 🔴 修复：恢复引擎的世界引用为大地图 ===
        if hasattr(self, '_world_map_ref'):
            self.engine.world = self._world_map_ref
            self.logger.debug("已恢复大地图引用")
        
        # === 🔴 修复：恢复玩家在大地图上的坐标 ===
        if hasattr(self, '_pre_location_pos') and self._pre_location_pos:
            # 恢复玩家坐标
            self.player.position.x = self._pre_location_pos.x
            self.player.position.y = self._pre_location_pos.y
            
            # === 🔴 修复：防止立即回吸，将玩家坐标稍微偏移，移出地点触发范围 ===
            # 向下偏移20像素，移出地点的触发范围（100像素）
            self.player.position.y += 20.0
            
            # 边界检查
            if hasattr(self.engine, 'world') and self.engine.world:
                self.player.position.x = max(0, min(self.engine.world.width, self.player.position.x))
                self.player.position.y = max(0, min(self.engine.world.height, self.player.position.y))
            
            self.logger.debug(f"已恢复玩家坐标并偏移: ({self.player.position.x}, {self.player.position.y})")
        else:
            self.logger.warning("没有找到进入地点前的玩家坐标，使用当前位置")
        
        # 清理状态
        self.current_location = None
        self.current_scene = 'world_map'
        
        # 清理保存的引用（可选，也可以保留以便重复进入）
        if hasattr(self, '_world_map_ref'):
            # 不删除，保留以便重复进入同一地点
            pass
        if hasattr(self, '_pre_location_pos'):
            # 不删除，保留以便重复进入
            pass
        
        # 恢复相机跟随玩家
        if self.player:
            self.window.follow_entity(self.player)
        
        self.logger.info(f"已返回大地图，玩家位置: ({self.player.position.x}, {self.player.position.y})")
    
    def render(self):
        """渲染游戏"""
        # 根据当前场景选择渲染方式
        if self.current_scene == 'world_map':
            # 大地图模式：只显示大地图实体（is_world_entity == True）
            world_npcs = [npc for npc in self.npcs if getattr(npc, 'is_world_entity', True)]
            self.window.draw_world_map(
                world=self.engine.world,
                player=self.player,
                locations=self.location_manager.get_all_locations(),
                npcs=world_npcs  # 只传递大地图NPC
            )
            # 绘制HUD
            self.window.draw_hud(self.player)
        elif self.current_scene == 'local_map':
            # 局部地图模式：只显示局部地图实体（is_world_entity == False）
            if self.current_view == GameView.WORLD:
                # 筛选局部地图实体（包括战斗遭遇的敌人）
                local_entities = []
                for entity in self.engine.entities:
                    # 包含玩家
                    if entity == self.player:
                        local_entities.append(entity)
                    # 包含局部地图NPC（非大地图实体）
                    elif isinstance(entity, NPC) and not getattr(entity, 'is_world_entity', True):
                        local_entities.append(entity)
                    # 包含战斗遭遇的敌人
                    elif hasattr(self, '_combat_enemy') and entity == self._combat_enemy:
                        local_entities.append(entity)
                    # 其他实体（如建筑等）
                    elif not isinstance(entity, NPC):
                        local_entities.append(entity)
                
                # 绘制世界
                local_world = self.current_location.local_map if self.current_location else self.engine.world
                self.window.draw_world(local_world, local_entities, self.player)
                # 绘制HUD
                self.window.draw_hud(self.player)
        
        elif self.current_view == GameView.MENU:
            # 绘制菜单
            menu_items = self.get_menu_items()
            items = [(key, text) for key, text in menu_items]
            self.window.draw_menu(items, self.menu_selected)
        
        elif self.current_view == GameView.DIALOG:
            # 绘制世界背景
            self.window.draw_world(self.engine.world, self.engine.entities)
            # 绘制对话界面
            if self.dialog_npc:
                # 如果是NPC遭遇对话框，显示选项
                options = None
                if hasattr(self, '_npc_encounter_choice_pending') and self._npc_encounter_choice_pending:
                    options = ["[1] 交谈", "[2] 交易", "[3] 攻击"]
                self.window.draw_dialog(self.dialog_npc, self.dialog_messages, self.dialog_input, options)
        
        elif self.current_view == GameView.TRADE:
            # 绘制世界背景
            self.window.draw_world(self.engine.world, self.engine.entities)
            # 绘制交易界面
            if self.trade_npc:
                self.window.draw_trade(self.player, self.trade_npc)
        
        # 绘制战斗提示消息（如果有）
        if hasattr(self, '_combat_message') and hasattr(self, '_combat_message_timer'):
            if self._combat_message_timer > 0:
                # 在屏幕中央显示战斗提示
                message_surface = self.window.font_medium.render(self._combat_message, True, (255, 0, 0))
                message_rect = message_surface.get_rect(center=(self.window.width // 2, 100))
                self.window.screen.blit(message_surface, message_rect)
        
        elif self.current_view == GameView.QUEST:
            # 绘制任务界面（简化）
            self.window.screen.fill(self.window.colors['black'])
            self.window.draw_text("任务列表", self.window.width // 2, 100,
                                self.window.colors['white'], self.window.font_large, center=True)
            
            active_quests = self.quest_manager.get_active_quests()
            y = 200
            for quest in active_quests:
                self.window.draw_text(f"{quest.title}", 50, y,
                                    self.window.colors['white'], self.window.font_medium)
                y += 40
        
        elif self.current_view == GameView.COLONY:
            # 绘制基地界面（使用预创建的覆盖层）
            self.window.screen.blit(self.window.overlay_bg, (0, 0))
            
            self.window.draw_text("基地管理", self.window.width // 2, 50,
                                self.window.colors['yellow'], self.window.font_large, center=True)
            
            y = 120
            
            # 资源显示
            if self.resource_manager:
                self.window.draw_text("【资源】", 50, y,
                                    self.window.colors['green'], self.window.font_medium)
                y += 40
                
                for resource_type, resource in self.resource_manager.resources.items():
                    if resource.amount > 0:
                        text = f"{resource_type.value}: {resource.amount:.1f}"
                        self.window.draw_text(text, 70, y,
                                            self.window.colors['white'], self.window.font_small)
                        y += 30
                
                y += 20
            
            # 建筑显示
            buildings = self.building_manager.buildings
            if buildings:
                self.window.draw_text("【建筑】", 50, y,
                                    self.window.colors['green'], self.window.font_medium)
                y += 40
                
                for building in buildings:
                    status = "已完成" if building.is_completed else "建造中"
                    health_status = f" (HP: {building.health}/{building.max_health})" if building.is_completed else ""
                    text = f"{building.building_type.value}: {status} Lv.{building.level}{health_status}"
                    self.window.draw_text(text, 70, y,
                                        self.window.colors['white'], self.window.font_small)
                    y += 30
            else:
                self.window.draw_text("【建筑】", 50, y,
                                    self.window.colors['green'], self.window.font_medium)
                y += 40
                self.window.draw_text("暂无建筑", 70, y,
                                    self.window.colors['gray'], self.window.font_small)
        
        # 更新显示
        self.window.update()
    
    def show_game_over(self):
        """显示游戏结束"""
        self.window.screen.fill(self.window.colors['black'])
        self.window.draw_text("游戏结束", self.window.width // 2, self.window.height // 2,
                            self.window.colors['red'], self.window.font_large, center=True)
        self.window.draw_text("按任意键退出", self.window.width // 2, self.window.height // 2 + 60,
                            self.window.colors['white'], self.window.font_medium, center=True)
        self.window.update()
        
        # 等待按键
        waiting = True
        while waiting:
            events = self.window.handle_events()
            if events is None:
                waiting = False
            for event in events:
                if event.type == pygame.KEYDOWN:
                    waiting = False
    
    def run(self):
        """运行游戏"""
        try:
            self.start()
        except KeyboardInterrupt:
            self.logger.info("游戏被用户中断")
        except Exception as e:
            self.logger.error(f"游戏运行出错: {e}")
            import traceback
            traceback_str = traceback.format_exc()
            self.logger.error(traceback_str)
            print(f"\n错误: {e}")
        finally:
            self.window.quit()
            self.logger.info("游戏结束")


def main():
    """游戏入口"""
    game = GameGUI()
    game.run()


if __name__ == "__main__":
    main()

