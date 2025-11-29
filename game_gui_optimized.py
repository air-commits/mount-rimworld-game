"""
图形界面游戏主控制器（优化版）
====================
只负责大地图显示和玩家移动
20x20地图，生成城镇、村庄、NPC
"""

import os
import sys
import time
import json
import pygame
from typing import Optional, Dict, Any

# 添加项目根目录到Python路径
_project_root = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, _project_root)

from core.game_engine import GameEngine
from core.world import Position, World
from entities.player import Player
from entities.npc import NPC
from core.locations import Location, LocationType
from ui.game_window import GameWindow, GameView
from assets_library import AssetsLibrary
from utils.logger import get_logger
from utils.config import get_config


class GameGUI:
    """
    图形界面游戏主控制器（优化版）
    ====================
    只负责大地图显示和玩家移动
    """
    
    def __init__(self):
        """初始化游戏"""
        self.logger = get_logger("GameGUI")
        self.config = get_config()
        
        # 初始化素材库
        self.assets = AssetsLibrary()
        
        # 初始化图形窗口
        self.window = GameWindow(width=1024, height=768)
        
        # 初始化核心系统
        self.engine = GameEngine(config_path="config.json")
        
        # 游戏数据
        self.player: Optional[Player] = None
        self.npcs: list = []  # NPC列表
        self.locations: list = []  # 地点列表（城镇、村庄）
        
        # 游戏状态
        self.running = False
        self.game_time = 0.0
        self.paused = False
        
        # 场景状态：'world_map' (大地图)
        self.current_scene = 'world_map'
        
        # 输入状态
        self.keys_pressed = {}
        self.mouse_pos = (0, 0)
        self.mouse_clicked = False
        
        # UI状态
        self.current_view = GameView.WORLD
        
        # 保存状态文件路径
        self.save_file = "game_state.json"
        
        # 地图尺寸（20x20瓦片）
        self.map_tiles = 20
        self.tile_size = 32  # 每个瓦片32像素
        self.map_width = self.map_tiles * self.tile_size  # 640像素
        self.map_height = self.map_tiles * self.tile_size  # 640像素
        
        self.logger.info("游戏GUI初始化完成（优化版）")
    
    def save_state(self) -> Dict[str, Any]:
        """
        保存当前游戏状态到文件
        
        【功能说明】
        - 将玩家数据、游戏时间、当前场景等信息保存到JSON文件
        - 用于界面切换时保存状态，切换回来后可以恢复
        
        Returns:
            Dict[str, Any]: 保存的游戏状态字典
        """
        self.logger.info("保存游戏状态到文件")
        
        state = {
            'player': {
                'name': self.player.name if self.player else "玩家",
                'position': {
                    'x': self.player.position.x if self.player else 0,
                    'y': self.player.position.y if self.player else 0
                },
                'health': getattr(self.player, 'health', 100) if self.player else 100,
                'money': getattr(self.player, 'money', 0) if self.player else 0,
            },
            'game_time': self.game_time,
            'current_scene': self.current_scene,
        }
        
        # 保存到文件
        try:
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            self.logger.info(f"游戏状态已保存到 {self.save_file}")
        except Exception as e:
            self.logger.error(f"保存游戏状态失败: {e}")
        
        return state
    
    def load_state(self) -> Optional[Dict[str, Any]]:
        """
        从文件加载游戏状态
        
        【功能说明】
        - 从JSON文件读取之前保存的游戏状态
        - 如果文件不存在或读取失败，返回None
        
        Returns:
            Optional[Dict[str, Any]]: 游戏状态字典，如果加载失败返回None
        """
        if not os.path.exists(self.save_file):
            self.logger.info("没有找到保存的游戏状态文件")
            return None
        
        try:
            with open(self.save_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            self.logger.info(f"从 {self.save_file} 加载游戏状态")
            return state
        except Exception as e:
            self.logger.error(f"加载游戏状态失败: {e}")
            return None
    
    def restore_state(self, saved_state: Dict[str, Any]):
        """
        恢复游戏状态
        
        【功能说明】
        - 从保存的状态字典中恢复玩家数据、游戏时间、场景等信息
        - 在从其他界面返回主地图时调用
        
        Args:
            saved_state: 保存的游戏状态字典
        """
        self.logger.info("恢复游戏状态")
        
        if not saved_state:
            return
        
        # 恢复玩家数据
        if 'player' in saved_state and self.player:
            player_data = saved_state['player']
            if 'position' in player_data:
                self.player.position.x = player_data['position'].get('x', self.player.position.x)
                self.player.position.y = player_data['position'].get('y', self.player.position.y)
            if 'health' in player_data:
                self.player.health = player_data['health']
            if 'money' in player_data:
                self.player.money = player_data['money']
        
        # 恢复游戏时间
        if 'game_time' in saved_state:
            self.game_time = saved_state['game_time']
        
        # 恢复场景
        if 'current_scene' in saved_state:
            self.current_scene = saved_state['current_scene']
        
        self.logger.info("游戏状态恢复完成")
    
    def initialize_world(self):
        """
        初始化游戏世界（20x20地图）
        
        【功能说明】
        - 创建20x20瓦片的地图（640x640像素）
        - 在地图中心创建玩家
        - 在玩家附近生成1个城镇、1个村庄
        - 在玩家附近生成3个NPC（中立、友好、敌对各1个）
        - 设置相机跟随玩家
        """
        self.logger.info("初始化游戏世界（20x20地图）...")
        
        # 创建20x20地图
        self.engine.world = World(width=self.map_width, height=self.map_height, tile_size=self.tile_size)
        self.logger.info(f"创建世界地图: {self.map_width}x{self.map_height} (20x20瓦片)")
        
        # 创建玩家（在地图中心）
        player_pos = Position(self.map_width // 2, self.map_height // 2)
        self.player = Player(name="玩家", position=player_pos)
        self.engine.add_entity(self.player)
        self.logger.info(f"玩家初始位置: ({player_pos.x}, {player_pos.y})")
        
        # 生成城镇（在玩家附近）
        town_pos = Position(player_pos.x + 100, player_pos.y - 100)
        town = Location(
            name="城镇",
            position=town_pos,
            location_type=LocationType.TOWN,
            faction="neutral",
            population=500
        )
        self.locations.append(town)
        self.logger.info(f"生成城镇: {town.name} 位置: ({town_pos.x}, {town_pos.y})")
        
        # 生成村庄（在玩家附近）
        village_pos = Position(player_pos.x - 100, player_pos.y + 100)
        village = Location(
            name="村庄",
            position=village_pos,
            location_type=LocationType.VILLAGE,
            faction="neutral",
            population=200
        )
        self.locations.append(village)
        self.logger.info(f"生成村庄: {village.name} 位置: ({village_pos.x}, {village_pos.y})")
        
        # 生成NPC（在玩家附近）
        # 中立NPC
        neutral_pos = Position(player_pos.x + 50, player_pos.y)
        neutral_npc = NPC(name="中立NPC", position=neutral_pos)
        neutral_npc.faction = "neutral"
        self.npcs.append(neutral_npc)
        self.engine.add_entity(neutral_npc)
        self.logger.info(f"生成中立NPC: {neutral_npc.name} 位置: ({neutral_pos.x}, {neutral_pos.y})")
        
        # 友好NPC
        friendly_pos = Position(player_pos.x, player_pos.y + 50)
        friendly_npc = NPC(name="友好NPC", position=friendly_pos)
        friendly_npc.faction = "alliance"
        self.npcs.append(friendly_npc)
        self.engine.add_entity(friendly_npc)
        self.logger.info(f"生成友好NPC: {friendly_npc.name} 位置: ({friendly_pos.x}, {friendly_pos.y})")
        
        # 敌对NPC
        enemy_pos = Position(player_pos.x - 50, player_pos.y)
        enemy_npc = NPC(name="敌对NPC", position=enemy_pos)
        enemy_npc.faction = "enemy"
        self.npcs.append(enemy_npc)
        self.engine.add_entity(enemy_npc)
        self.logger.info(f"生成敌对NPC: {enemy_npc.name} 位置: ({enemy_pos.x}, {enemy_pos.y})")
        
        # 相机跟随玩家
        self.window.follow_entity(self.player)
        
        self.logger.info("游戏世界初始化完成")
    
    def start(self):
        """
        启动游戏
        
        【功能说明】
        - 初始化游戏世界
        - 开始游戏主循环
        - 这是游戏的入口点
        """
        self.logger.info("=" * 50)
        self.logger.info("骑砍环世界融合游戏（优化版）启动")
        self.logger.info("=" * 50)
        
        # 初始化世界
        self.initialize_world()
        
        # 开始游戏循环
        self.running = True
        self.game_loop()
    
    def game_loop(self):
        """
        游戏主循环
        
        【功能说明】
        - 游戏的核心循环，每帧执行以下操作：
          1. 计算时间差（delta_time）
          2. 更新游戏时间（如果未暂停）
          3. 处理事件（键盘、鼠标）
          4. 更新游戏逻辑（如果未暂停）
          5. 绘制画面
          6. 更新显示
        - 限制帧率为60FPS
        - 异常处理和状态保存
        """
        clock = pygame.time.Clock()
        last_time = time.time()
        
        try:
            while self.running:
                current_time = time.time()
                delta_time = current_time - last_time
                last_time = current_time
                
                # 限制帧率
                delta_time = min(delta_time, 0.1)
                
                # 更新游戏时间
                if not self.paused:
                    self.game_time += delta_time
                
                # 处理事件
                self.handle_events()
                
                # 更新游戏逻辑
                if not self.paused:
                    self.update(delta_time)
                
                # 绘制
                self.draw()
                
                # 更新显示
                pygame.display.flip()
                clock.tick(60)
        
        except Exception as e:
            self.logger.error(f"游戏运行出错: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        finally:
            # 退出前保存状态
            self.save_state()
            self.quit()
    
    def handle_events(self):
        """
        处理Pygame事件
        
        【功能说明】
        - 处理窗口关闭事件（QUIT）
        - 处理键盘按下事件（KEYDOWN）
        - 处理鼠标点击事件（MOUSEBUTTONDOWN/UP）
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event.key, event.mod)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_clicked = True
                self.mouse_pos = event.pos
                if event.button == 1:  # 左键
                    self.handle_mouse_click(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.mouse_clicked = False
    
    def handle_keydown(self, key: int, mod: int):
        """
        处理键盘按键事件
        
        Args:
            key: 按键代码（pygame.K_*）
            mod: 修饰键（Shift、Ctrl等）
        
        【当前支持的按键】
        - ESC: 暂停/取消暂停游戏
        """
        # ESC: 暂停/取消暂停
        if key == pygame.K_ESCAPE:
            self.paused = not self.paused
    
    def handle_mouse_click(self, pos: tuple):
        """
        处理鼠标点击事件（主要用于底部按钮）
        
        Args:
            pos: 鼠标点击位置 (x, y)
        
        【功能说明】
        - 检测点击是否在底部按钮区域内
        - 如果点击了按钮，调用 handle_button_click() 处理
        """
        button_y = self.window.height - 60
        button_height = 50
        button_width = 140
        button_spacing = 10
        
        buttons = [
            ("设置", "settings"),
            ("暂停" if not self.paused else "开始", "pause"),
            ("背包", "inventory"),
            ("军队", "army"),
            ("国家", "nation"),
            ("关系", "relations"),
        ]
        
        start_x = (self.window.width - (len(buttons) * (button_width + button_spacing) - button_spacing)) // 2
        
        for i, (text, action) in enumerate(buttons):
            button_x = start_x + i * (button_width + button_spacing)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            
            if button_rect.collidepoint(pos):
                self.handle_button_click(action)
                break
    
    def handle_button_click(self, action: str):
        """
        处理底部按钮点击事件
        
        Args:
            action: 按钮动作名称（"pause", "settings", "inventory"等）
        
        【支持的按钮动作】
        - pause: 暂停/继续游戏
        - settings: 切换到设置界面
        - inventory: 切换到背包界面
        - army: 切换到军队界面
        - nation: 切换到国家界面
        - relations: 切换到关系界面
        """
        if action == "pause":
            self.paused = not self.paused
            self.logger.info(f"游戏{'暂停' if self.paused else '继续'}")
        elif action == "settings":
            self.switch_to_interface("settings")
        elif action == "inventory":
            self.switch_to_interface("inventory")
        elif action == "army":
            self.switch_to_interface("army")
        elif action == "nation":
            self.switch_to_interface("nation")
        elif action == "relations":
            self.switch_to_interface("relations")
    
    def switch_to_interface(self, interface_name: str):
        """
        切换到指定的功能界面
        
        Args:
            interface_name: 界面名称（"settings", "inventory", "army"等）
        
        【功能说明】
        - 保存当前游戏状态
        - 创建并运行对应的界面主程序
        - 界面返回后恢复游戏状态
        - 恢复相机跟随玩家
        """
        self.logger.info(f"切换到{interface_name}界面")
        saved_state = self.save_state()
        
        try:
            if interface_name == "settings":
                from settings_main import SettingsMain
                interface = SettingsMain(saved_state)
            elif interface_name == "inventory":
                from inventory_main import InventoryMain
                interface = InventoryMain(saved_state)
            elif interface_name == "army":
                from army_main import ArmyMain
                interface = ArmyMain(saved_state)
            elif interface_name == "nation":
                from nation_main import NationMain
                interface = NationMain(saved_state)
            elif interface_name == "relations":
                from relations_main import RelationsMain
                interface = RelationsMain(saved_state)
            else:
                return
            
            result = interface.run()
            self.restore_state(result)
            if self.player:
                self.window.follow_entity(self.player)
        except Exception as e:
            self.logger.error(f"切换界面失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def draw_bottom_buttons(self):
        """
        绘制底部按钮栏
        
        【功能说明】
        - 在窗口底部绘制6个功能按钮：
          1. 设置
          2. 暂停/开始
          3. 背包
          4. 军队
          5. 国家
          6. 关系
        - 按钮居中排列，带边框和文字
        """
        button_y = self.window.height - 60
        button_height = 50
        button_width = 140
        button_spacing = 10
        
        buttons = [
            ("设置", "settings"),
            ("暂停" if not self.paused else "开始", "pause"),
            ("背包", "inventory"),
            ("军队", "army"),
            ("国家", "nation"),
            ("关系", "relations"),
        ]
        
        start_x = (self.window.width - (len(buttons) * (button_width + button_spacing) - button_spacing)) // 2
        
        for i, (text, action) in enumerate(buttons):
            button_x = start_x + i * (button_width + button_spacing)
            
            # 绘制按钮背景
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            pygame.draw.rect(self.window.screen, (60, 60, 60), button_rect)
            pygame.draw.rect(self.window.screen, (200, 200, 200), button_rect, 2)
            
            # 绘制按钮文字
            button_text = self.window.font_small.render(text, True, (255, 255, 255))
            text_rect = button_text.get_rect(center=button_rect.center)
            self.window.screen.blit(button_text, text_rect)
    
    def update(self, delta_time: float):
        """
        更新游戏逻辑
        
        Args:
            delta_time: 上一帧到这一帧的时间差（秒）
        
        【功能说明】
        - 处理玩家移动（WASD/方向键）
        - 检测地图边界（空气墙）
        - 检查地形碰撞
        - 更新游戏引擎
        - 相机跟随玩家
        """
        if not self.player:
            return
        
        # 处理玩家移动
        move_speed = 200.0
        move_delta = move_speed * delta_time
        
        # 获取按键状态
        keys = pygame.key.get_pressed()
        
        # 计算移动方向
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= move_delta
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += move_delta
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= move_delta
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += move_delta
        
        # 应用移动（带空气墙检测）
        if dx != 0 or dy != 0:
            new_x = self.player.position.x + dx
            new_y = self.player.position.y + dy
            
            # 空气墙检测（20x20地图边界）
            new_x = max(0, min(self.map_width - 1, new_x))
            new_y = max(0, min(self.map_height - 1, new_y))
            
            new_pos = Position(new_x, new_y)
            
            # 检查是否可以移动
            if self.engine.world.can_move_to(new_pos):
                self.player.position.x = new_x
                self.player.position.y = new_y
                self.window.follow_entity(self.player)
        
        # 更新引擎
        self.engine.update(delta_time)
    
    def draw(self):
        """
        绘制游戏画面
        
        【功能说明】
        - 根据当前视图模式绘制不同的内容
        - WORLD视图：绘制地图、实体、地点、HUD、底部按钮
        - 使用素材库加载资源，如果没有素材则使用默认图形
        """
        if self.current_view == GameView.WORLD:
            if self.engine.world and self.player:
                # 收集所有实体（玩家、NPC、地点）
                entities = [self.player] + self.npcs
                
                # 绘制大地图
                self.window.draw_world_with_assets(
                    self.engine.world,
                    entities,
                    self.locations,
                    self.player,
                    self.assets
                )
                
                # 绘制HUD和底部按钮栏
                self.window.draw_hud(self.player)
                self.draw_bottom_buttons()
    
    def quit(self):
        """
        退出游戏
        
        【功能说明】
        - 关闭Pygame窗口
        - 记录日志
        - 在 game_loop() 的 finally 块中调用
        """
        self.logger.info("游戏窗口已关闭")
        self.logger.info("游戏结束")
        pygame.quit()


def main():
    """
    主函数（程序入口点）
    
    【使用方式】
    运行此文件即可启动游戏：
        python game_gui_optimized.py
    """
    game = GameGUI()
    game.start()


if __name__ == "__main__":
    main()
