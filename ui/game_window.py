"""
游戏图形窗口
使用pygame实现的图形界面
"""

import pygame
import os
from typing import Optional, List, Dict, Tuple
from enum import Enum

from core.world import Position, World, TerrainType
from core.locations import Location
from entities.player import Player
from entities.npc import NPC
from utils.logger import get_logger
# 小地图已移除，不再导入


class GameView(Enum):
    """游戏视图模式"""
    WORLD = "world"          # 世界视图
    MENU = "menu"            # 菜单视图
    INVENTORY = "inventory"  # 背包视图
    QUEST = "quest"          # 任务视图
    COLONY = "colony"        # 基地视图
    DIALOG = "dialog"        # 对话视图
    TRADE = "trade"         # 交易视图


class GameWindow:
    """游戏图形窗口"""
    
    def __init__(self, width: int = 1024, height: int = 768):
        """
        初始化游戏窗口
        
        Args:
            width: 窗口宽度
            height: 窗口高度
        """
        # === 🔴 修复：将 Logger 初始化移到第一行 ===
        # 必须先初始化 logger，因为后面的 _load_font 需要用到它
        self.logger = get_logger("GameWindow")
        
        pygame.init()
        
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("骑砍环世界融合游戏")
        
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # 字体初始化（支持中文显示）
        # 现在调用 _load_font 是安全的，因为 logger 已经存在了
        self.font_small = self._load_font(24)
        self.font_medium = self._load_font(32)
        self.font_large = self._load_font(48)
        
        # 颜色定义
        self.colors = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'gray': (128, 128, 128),
            'light_gray': (200, 200, 200),
            'dark_gray': (64, 64, 64),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'brown': (139, 69, 19),
            'grass': (34, 139, 34),  # 草地颜色（唯一使用）
        }
        
        # 当前视图
        self.current_view = GameView.WORLD
        
        # 相机位置（世界坐标）
        self.camera_x = 0
        self.camera_y = 0
        
        # 缩放级别
        self.zoom = 1.0
        
        # 地图瓦片大小
        self.tile_size = 32
        
        # 选中实体（保留用于未来功能）
        self.selected_entity = None
        
        # === 性能优化：预创建半透明蒙版，避免每帧重复创建 ===
        # 1. 全屏蒙版 (用于菜单/对话)
        self.overlay_bg = pygame.Surface((self.width, self.height))
        self.overlay_bg.set_alpha(200)
        self.overlay_bg.fill(self.colors['black'])
        
        # 2. HUD顶部条蒙版
        self.hud_top_bg = pygame.Surface((self.width, 80))
        self.hud_top_bg.set_alpha(200)
        self.hud_top_bg.fill(self.colors['black'])
        
        # 3. HUD底部条蒙版
        self.hud_bottom_bg = pygame.Surface((self.width, 40))
        self.hud_bottom_bg.set_alpha(200)
        self.hud_bottom_bg.fill(self.colors['black'])
        
        # 日志初始化已移至最上方，此处删除原来的初始化代码
        
        self.logger.info("游戏窗口初始化完成")
    
    def _load_font(self, size: int):
        """
        加载字体（支持中文显示）
        
        Args:
            size: 字体大小
            
        Returns:
            Font对象
        """
        # 1. 优先尝试使用系统自带的中文字体
        chinese_fonts = [
            'simhei',           # 黑体（Windows/Linux常见）
            'microsoftyahei',    # 微软雅黑（Windows）
            'simsun',           # 宋体（Windows）
            'kaiti',            # 楷体（Windows）
            'fangsong',         # 仿宋（Windows）
            'STHeiti',          # 黑体（macOS）
            'PingFang SC',      # 苹方（macOS）
            'WenQuanYi Micro Hei',  # 文泉驿微米黑（Linux）
            'Noto Sans CJK SC',     # Noto字体（Linux）
        ]
        
        for font_name in chinese_fonts:
            try:
                font = pygame.font.SysFont(font_name, size)
                # 测试字体是否支持中文（渲染一个中文字符）
                test_surface = font.render('中', True, (255, 255, 255))
                if test_surface.get_width() > 0:
                    self.logger.debug(f"成功加载中文字体: {font_name} (大小: {size})")
                    return font
            except Exception as e:
                self.logger.debug(f"尝试加载字体 {font_name} 失败: {e}")
                continue
        
        # 2. 尝试加载本地字体文件（如果存在）
        local_font_paths = [
            'assets/font.ttf',
            'assets/fonts/simhei.ttf',
            'assets/fonts/msyh.ttf',
            'font.ttf',
        ]
        
        for font_path in local_font_paths:
            try:
                if os.path.exists(font_path):
                    font = pygame.font.Font(font_path, size)
                    self.logger.info(f"成功加载本地字体文件: {font_path} (大小: {size})")
                    return font
            except Exception as e:
                self.logger.debug(f"尝试加载本地字体 {font_path} 失败: {e}")
                continue
        
        # 3. 保底方案：使用默认字体（可能不支持中文，但不报错）
        self.logger.warning(f"未能加载中文字体，使用默认字体（可能不支持中文显示）")
        return pygame.font.Font(None, size)
    
    def world_to_screen(self, world_pos: Position) -> Tuple[int, int]:
        """
        将世界坐标转换为屏幕坐标
        
        Args:
            world_pos: 世界坐标
            
        Returns:
            屏幕坐标 (x, y)
        """
        screen_x = int((world_pos.x - self.camera_x) * self.zoom + self.width / 2)
        screen_y = int((world_pos.y - self.camera_y) * self.zoom + self.height / 2)
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> Position:
        """
        将屏幕坐标转换为世界坐标
        
        Args:
            screen_x: 屏幕X坐标
            screen_y: 屏幕Y坐标
            
        Returns:
            世界坐标
        """
        world_x = (screen_x - self.width / 2) / self.zoom + self.camera_x
        world_y = (screen_y - self.height / 2) / self.zoom + self.camera_y
        return Position(world_x, world_y)
    
    def follow_entity(self, entity):
        """
        相机跟随实体
        
        Args:
            entity: 要跟随的实体
        """
        if entity:
            self.camera_x = entity.position.x
            self.camera_y = entity.position.y
    
    def draw_text(self, text: str, x: int, y: int, color: Tuple = None, font=None, center: bool = False):
        """
        绘制文本
        
        Args:
            text: 文本内容
            x: X坐标
            y: Y坐标
            color: 颜色（默认白色）
            font: 字体（默认中等字体）
            center: 是否居中
        """
        if color is None:
            color = self.colors['white']
        if font is None:
            font = self.font_medium
        
        text_surface = font.render(str(text), True, color)
        if center:
            text_rect = text_surface.get_rect(center=(x, y))
            self.screen.blit(text_surface, text_rect)
        else:
            self.screen.blit(text_surface, (x, y))
    
    def draw_world(self, world, entities: List, player: Player = None):
        """
        绘制世界（局部地图）
        
        Args:
            world: 世界对象
            entities: 实体列表
            player: 玩家对象（可选，用于相机跟随）
        """
        self.screen.fill(self.colors['dark_gray'])
        
        # 边界检查
        if not hasattr(world, 'terrain_grid') or not world.terrain_grid:
            self.logger.warning("世界地形网格为空，无法绘制")
            return
        
        # 计算视口范围
        tl = self.screen_to_world(0, 0)
        br = self.screen_to_world(self.width, self.height)
        
        grid_width = len(world.terrain_grid[0]) if world.terrain_grid else 0
        grid_height = len(world.terrain_grid) if world.terrain_grid else 0
        
        start_x = max(0, int(tl.x // world.tile_size) - 2)
        end_x = min(grid_width, int(br.x // world.tile_size) + 2)
        start_y = max(0, int(tl.y // world.tile_size) - 2)
        end_y = min(grid_height, int(br.y // world.tile_size) + 2)
        
        # 绘制地形（全部为白色地板瓦片）
        tile_size_scaled = int(self.tile_size * self.zoom)
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                # 边界检查
                if y >= grid_height or x >= grid_width:
                    continue
                
                # 计算世界坐标和屏幕坐标
                wx, wy = x * world.tile_size, y * world.tile_size
                scx, scy = self.world_to_screen(Position(wx, wy))
                
                # 绘制地块（白色地板）
                pygame.draw.rect(self.screen, (255, 255, 255), (
                    int(scx - self.tile_size // 2), int(scy - self.tile_size // 2),
                    tile_size_scaled, tile_size_scaled
                ))
        
        # 绘制实体
        for ent in entities:
            if not getattr(ent, 'is_alive', True):
                continue
            ex, ey = self.world_to_screen(ent.position)
            if -50 < ex < self.width + 50 and -50 < ey < self.height + 50:
                col = self.colors['blue'] if isinstance(ent, Player) else self.colors['green']
                pygame.draw.circle(self.screen, col, (int(ex), int(ey)), 8)
                if hasattr(ent, 'name'):
                    self.draw_text(ent.name, int(ex), int(ey) - 20, center=True, font=self.font_small)
    
    def draw_world_with_assets(self, world, entities: List, locations: List, player: Player = None, assets=None):
        """
        绘制世界（带素材支持）
        
        Args:
            world: 世界对象
            entities: 实体列表（玩家、NPC）
            locations: 地点列表（城镇、村庄）
            player: 玩家对象
            assets: 素材库对象
        """
        self.screen.fill(self.colors['dark_gray'])
        
        # 计算视口范围
        tl = self.screen_to_world(0, 0)
        br = self.screen_to_world(self.width, self.height)
        
        start_x = max(0, int(tl.x // world.tile_size) - 2)
        end_x = min(world.width // world.tile_size, int(br.x // world.tile_size) + 2)
        start_y = max(0, int(tl.y // world.tile_size) - 2)
        end_y = min(world.height // world.tile_size, int(br.y // world.tile_size) + 2)
        
        # 绘制地形（白色地板瓦片）
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if y >= len(world.terrain_grid) or x >= len(world.terrain_grid[0]):
                    continue
                
                # 计算世界坐标和屏幕坐标
                wx, wy = x * world.tile_size, y * world.tile_size
                scx, scy = self.world_to_screen(Position(wx, wy))
                
                # 尝试加载地图素材，没有就用白色地板
                map_asset = assets.get_map_asset("floor") if assets else None
                if map_asset and os.path.exists(map_asset):
                    try:
                        tile_img = pygame.image.load(map_asset)
                        tile_img = pygame.transform.scale(tile_img, (int(self.tile_size * self.zoom), int(self.tile_size * self.zoom)))
                        self.screen.blit(tile_img, (int(scx - self.tile_size // 2), int(scy - self.tile_size // 2)))
                    except:
                        # 加载失败，使用白色地板
                        pygame.draw.rect(self.screen, (255, 255, 255), (
                            int(scx - self.tile_size // 2), int(scy - self.tile_size // 2),
                            int(self.tile_size * self.zoom), int(self.tile_size * self.zoom)
                        ))
                else:
                    # 没有素材，使用白色地板
                    pygame.draw.rect(self.screen, (255, 255, 255), (
                        int(scx - self.tile_size // 2), int(scy - self.tile_size // 2),
                        int(self.tile_size * self.zoom), int(self.tile_size * self.zoom)
                    ))
        
        # 绘制地点（城镇、村庄）
        for location in locations:
            lx, ly = self.world_to_screen(location.position)
            if -50 < lx < self.width + 50 and -50 < ly < self.height + 50:
                # 尝试加载地点素材
                loc_asset = assets.get_location_asset(location.name) if assets else None
                if loc_asset and os.path.exists(loc_asset):
                    try:
                        loc_img = pygame.image.load(loc_asset)
                        loc_img = pygame.transform.scale(loc_img, (32, 32))
                        self.screen.blit(loc_img, (int(lx - 16), int(ly - 16)))
                    except Exception as e:
                        # 加载失败，使用黑方块
                        self.logger.debug(f"加载地点素材失败: {e}")
                        pygame.draw.rect(self.screen, (0, 0, 0), (int(lx - 16), int(ly - 16), 32, 32))
                        self.draw_text(location.name, int(lx), int(ly - 25), center=True, font=self.font_small)
                else:
                    # 没有素材，使用黑方块
                    pygame.draw.rect(self.screen, (0, 0, 0), (int(lx - 16), int(ly - 16), 32, 32))
                    self.draw_text(location.name, int(lx), int(ly - 25), center=True, font=self.font_small)
        
        # 绘制实体（玩家、NPC）
        for ent in entities:
            if not getattr(ent, 'is_alive', True):
                continue
            ex, ey = self.world_to_screen(ent.position)
            if -50 < ex < self.width + 50 and -50 < ey < self.height + 50:
                # 判断是玩家还是NPC
                if isinstance(ent, Player):
                    # 玩家：尝试加载角色素材
                    char_asset = assets.get_character_asset("player") if assets else None
                    if char_asset and os.path.exists(char_asset):
                        try:
                            char_img = pygame.image.load(char_asset)
                            char_img = pygame.transform.scale(char_img, (32, 32))
                            self.screen.blit(char_img, (int(ex - 16), int(ey - 16)))
                        except Exception as e:
                            # 加载失败，使用黑方块
                            self.logger.debug(f"加载角色素材失败: {e}")
                            pygame.draw.rect(self.screen, (0, 0, 0), (int(ex - 16), int(ey - 16), 32, 32))
                            if hasattr(ent, 'name'):
                                self.draw_text(ent.name, int(ex), int(ey - 25), center=True, font=self.font_small)
                    else:
                        # 没有素材，使用黑方块
                        pygame.draw.rect(self.screen, (0, 0, 0), (int(ex - 16), int(ey - 16), 32, 32))
                        if hasattr(ent, 'name'):
                            self.draw_text(ent.name, int(ex), int(ey - 25), center=True, font=self.font_small)
                else:
                    # NPC：尝试加载NPC素材
                    npc_asset = assets.get_npc_asset(ent.name) if assets else None
                    if npc_asset and os.path.exists(npc_asset):
                        try:
                            npc_img = pygame.image.load(npc_asset)
                            npc_img = pygame.transform.scale(npc_img, (32, 32))
                            self.screen.blit(npc_img, (int(ex - 16), int(ey - 16)))
                        except Exception as e:
                            # 加载失败，使用黑方块
                            self.logger.debug(f"加载NPC素材失败: {e}")
                            pygame.draw.rect(self.screen, (0, 0, 0), (int(ex - 16), int(ey - 16), 32, 32))
                            if hasattr(ent, 'name'):
                                self.draw_text(ent.name, int(ex), int(ey - 25), center=True, font=self.font_small)
                    else:
                        # 没有素材，使用黑方块
                        pygame.draw.rect(self.screen, (0, 0, 0), (int(ex - 16), int(ey - 16), 32, 32))
                        if hasattr(ent, 'name'):
                            self.draw_text(ent.name, int(ex), int(ey - 25), center=True, font=self.font_small)
    
    