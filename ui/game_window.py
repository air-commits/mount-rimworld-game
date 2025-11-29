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
    
    def draw_world_map(
        self,
        world: World,
        player: Player,
        locations: List[Location],
        npcs: Optional[List[NPC]] = None
    ):
        """
        绘制大地图（骑马与砍杀风格）
        
        Args:
            world: 世界对象
            player: 玩家对象（显示为军团图标）
            locations: 地点列表
            npcs: NPC列表（其他军团，可选）
        """
        # === 🔴 紧急修复：第一行清空屏幕，防止残影（拉丝） ===
        self.screen.fill((0, 0, 0))  # 使用黑色填充，确保完全清空
        
        # 绘制大地图地形背景
        self._draw_global_map_terrain(world)
        
        # === 优化：先绘制所有图标，再统一绘制文字，防止重叠 ===
        # 收集所有需要绘制的文字标签（位置、文字、颜色）
        text_labels = []
        
        # 绘制地点图标
        for location in locations:
            screen_x, screen_y = self.world_to_screen(location.position)
            
            # 只绘制可见的地点
            if -100 <= screen_x <= self.width + 100 and -100 <= screen_y <= self.height + 100:
                # 根据地点类型选择颜色和图标
                if location.location_type.value == "town":
                    color = (255, 215, 0)  # 金黄色
                    size = 14
                    icon_char = "城"
                elif location.location_type.value == "village":
                    color = (144, 238, 144)  # 浅绿色
                    size = 12
                    icon_char = "村"
                elif location.location_type.value == "resource_point":
                    color = (160, 82, 45)  # 棕色
                    size = 10
                    icon_char = "资"
                elif location.location_type.value == "dungeon":
                    color = (220, 20, 60)  # 深红色
                    size = 12
                    icon_char = "牢"
                else:
                    color = self.colors['gray']
                    size = 10
                    icon_char = "点"
                
                # 绘制地点图标（更大的圆点，带阴影效果）
                # 阴影（使用半透明黑色）
                shadow_surface = pygame.Surface((size * 2 + 4, size * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(shadow_surface, (0, 0, 0, 100), 
                                 (size + 2, size + 2), size)
                self.screen.blit(shadow_surface, (int(screen_x) - size - 2, int(screen_y) - size - 2))
                
                # 主体
                pygame.draw.circle(self.screen, color, 
                                 (int(screen_x), int(screen_y)), size)
                pygame.draw.circle(self.screen, (255, 255, 255), 
                                 (int(screen_x), int(screen_y)), size, 2)
                
                # 绘制地点类型标识（放在图标内）
                icon_surface = self.font_small.render(icon_char, True, (255, 255, 255))
                icon_rect = icon_surface.get_rect(center=(int(screen_x), int(screen_y)))
                self.screen.blit(icon_surface, icon_rect)
                
                # 收集文字标签，稍后统一绘制
                text_labels.append({
                    'text': location.name,
                    'x': int(screen_x),
                    'y': int(screen_y) - 30,
                    'color': self.colors['white'],
                    'center': True
                })
        
        # 绘制玩家军团图标（蓝色圆点，更大更醒目）
        player_screen_x, player_screen_y = self.world_to_screen(player.position)
        # 阴影
        shadow_surface = pygame.Surface((24 + 4, 24 + 4), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surface, (0, 0, 0, 100), 
                         (12 + 2, 12 + 2), 12)
        self.screen.blit(shadow_surface, (int(player_screen_x) - 12 - 2, int(player_screen_y) - 12 - 2))
        
        # 主体
        pygame.draw.circle(self.screen, (0, 100, 255), 
                         (int(player_screen_x), int(player_screen_y)), 12)
        pygame.draw.circle(self.screen, (255, 255, 255), 
                         (int(player_screen_x), int(player_screen_y)), 12, 2)
        
        # 收集玩家文字标签
        text_labels.append({
            'text': player.name,
            'x': int(player_screen_x),
            'y': int(player_screen_y) - 30,
            'color': (0, 150, 255),
            'center': True
        })
        
        # 绘制队伍大小（如果有多个成员）
        if hasattr(player, 'get_party_size') and player.get_party_size() > 1:
            party_size_text = f"({player.get_party_size()}人)"
            text_labels.append({
                'text': party_size_text,
                'x': int(player_screen_x),
                'y': int(player_screen_y) + 18,
                'color': self.colors['light_gray'],
                'center': True
            })
        
        # 绘制其他NPC军团图标（如果有）
        if npcs:
            for npc in npcs:
                if not hasattr(npc, 'is_alive') or not npc.is_alive:
                    continue
                
                npc_screen_x, npc_screen_y = self.world_to_screen(npc.position)
                
                # 只绘制可见的NPC
                if -50 <= npc_screen_x <= self.width + 50 and -50 <= npc_screen_y <= self.height + 50:
                    # 根据NPC的faction选择颜色
                    npc_faction = getattr(npc, 'faction', 'neutral')
                    if npc_faction in ['enemy', 'bandit']:
                        npc_color = (255, 50, 50)  # 红色（敌对）
                    else:
                        npc_color = (50, 200, 50)  # 绿色（中立/友善）
                    
                    # NPC军团图标（带阴影）
                    shadow_surface = pygame.Surface((18 + 2, 18 + 2), pygame.SRCALPHA)
                    pygame.draw.circle(shadow_surface, (0, 0, 0, 100), 
                                     (9 + 1, 9 + 1), 9)
                    self.screen.blit(shadow_surface, (int(npc_screen_x) - 9 - 1, int(npc_screen_y) - 9 - 1))
                    
                    pygame.draw.circle(self.screen, npc_color, 
                                     (int(npc_screen_x), int(npc_screen_y)), 9)
                    pygame.draw.circle(self.screen, (255, 255, 255), 
                                     (int(npc_screen_x), int(npc_screen_y)), 9, 1)
                    
                    # 收集NPC文字标签
                    text_labels.append({
                        'text': npc.name,
                        'x': int(npc_screen_x),
                        'y': int(npc_screen_y) - 25,
                        'color': npc_color,
                        'center': True
                    })
        
        # === 统一绘制所有文字标签（在所有图标之后，防止重叠） ===
        for label in text_labels:
            self._draw_text_with_outline(
                label['text'],
                label['x'],
                label['y'],
                label['color'],
                self.font_small,
                center=label.get('center', False)
            )
        
        # 绘制提示文本（底部，带半透明背景，向上移动避免与HUD重叠）
        hint_text = "按 [F] 进入地点 | 按 [TAB] 切换视图"
        hint_surface = self.font_small.render(hint_text, True, self.colors['light_gray'])
        hint_rect = hint_surface.get_rect(center=(self.width // 2, self.height - 100))
        
        # 绘制半透明背景
        hint_bg = pygame.Surface((hint_rect.width + 20, hint_rect.height + 10))
        hint_bg.set_alpha(180)
        hint_bg.fill((0, 0, 0))
        self.screen.blit(hint_bg, (hint_rect.x - 10, hint_rect.y - 5))
        self.screen.blit(hint_surface, hint_rect)
        
        # === 确保不绘制小地图（大地图模式下完全隐藏） ===
        # 不调用 self.minimap.draw()
    
    def _draw_global_map_terrain(self, world: World):
        """
        绘制大地图地形背景
        
        Args:
            world: 世界对象
        """
        if not hasattr(world, 'global_map_grid') or not world.global_map_grid:
            # 如果没有大地图地形数据，使用默认背景
            self.screen.fill(self.colors['dark_gray'])
            return
        
        # 获取可见区域的世界坐标范围
        top_left_world = self.screen_to_world(0, 0)
        bottom_right_world = self.screen_to_world(self.width, self.height)
        
        # 计算需要绘制的网格范围
        global_grid_width = len(world.global_map_grid[0]) if world.global_map_grid else 0
        global_grid_height = len(world.global_map_grid) if world.global_map_grid else 0
        
        start_x = max(0, int(top_left_world.x // world.global_map_tile_size) - 1)
        end_x = min(global_grid_width, int(bottom_right_world.x // world.global_map_tile_size) + 2)
        start_y = max(0, int(top_left_world.y // world.global_map_tile_size) - 1)
        end_y = min(global_grid_height, int(bottom_right_world.y // world.global_map_tile_size) + 2)
        
        # 地形颜色映射
        terrain_colors = {
            'grass': (46, 125, 50),      # 深绿色
            'forest': (27, 94, 32),      # 更深绿色
            'water': (21, 101, 192),     # 深蓝色
            'mountain': (97, 97, 97),    # 灰褐色
            'desert': (176, 126, 68),    # 沙漠色
        }
        
        # 绘制地形瓦片
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if y >= global_grid_height or x >= global_grid_width:
                    continue
                
                terrain = world.global_map_grid[y][x]
                terrain_name = terrain.value if hasattr(terrain, 'value') else str(terrain)
                color = terrain_colors.get(terrain_name, terrain_colors['grass'])
                
                # 转换为屏幕坐标
                world_x = x * world.global_map_tile_size
                world_y = y * world.global_map_tile_size
                screen_x, screen_y = self.world_to_screen(Position(world_x, world_y))
                
                # 绘制地形矩形
                tile_rect = pygame.Rect(
                    int(screen_x - world.global_map_tile_size // 2 * self.zoom),
                    int(screen_y - world.global_map_tile_size // 2 * self.zoom),
                    int(world.global_map_tile_size * self.zoom),
                    int(world.global_map_tile_size * self.zoom)
                )
                pygame.draw.rect(self.screen, color, tile_rect)
    
    def _draw_text_with_outline(self, text: str, x: int, y: int, color: Tuple = None, 
                                font=None, center: bool = False, outline_color: Tuple = None):
        """
        绘制带描边的文字（提高可读性）
        
        Args:
            text: 文本内容
            x: X坐标
            y: Y坐标
            color: 文字颜色（默认白色）
            font: 字体（默认中等字体）
            center: 是否居中
            outline_color: 描边颜色（默认黑色）
        """
        if color is None:
            color = self.colors['white']
        if font is None:
            font = self.font_small
        if outline_color is None:
            outline_color = (0, 0, 0)
        
        # 渲染文字
        text_surface = font.render(str(text), True, color)
        
        # 创建描边效果（在8个方向绘制黑色文字）
        outline_offset = [(0, 1), (0, -1), (1, 0), (-1, 0), 
                         (1, 1), (-1, -1), (1, -1), (-1, 1)]
        
        outline_surface = font.render(str(text), True, outline_color)
        
        if center:
            text_rect = text_surface.get_rect(center=(x, y))
            # 先绘制描边
            for offset_x, offset_y in outline_offset:
                outline_rect = outline_surface.get_rect(center=(x + offset_x, y + offset_y))
                self.screen.blit(outline_surface, outline_rect)
            # 再绘制文字
            self.screen.blit(text_surface, text_rect)
        else:
            # 先绘制描边
            for offset_x, offset_y in outline_offset:
                self.screen.blit(outline_surface, (x + offset_x, y + offset_y))
            # 再绘制文字
            self.screen.blit(text_surface, (x, y))
    
    def draw_hud(self, player: Player):
        """
        绘制HUD（抬头显示）
        
        Args:
            player: 玩家对象
        """
        # 使用预创建的顶部信息栏背景（性能优化）
        self.screen.blit(self.hud_top_bg, (0, 0))
        
        # 玩家基本信息
        info_text = f"{player.name} (Lv.{player.level}) | 金币: {player.money}"
        self.draw_text(info_text, 10, 10, self.colors['white'], self.font_small)
        
        # 生命值条
        hp_bar_x = 10
        hp_bar_y = 35
        hp_bar_width = 300
        hp_bar_height = 20
        
        # 背景
        pygame.draw.rect(self.screen, self.colors['dark_gray'],
                        (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height))
        
        # 生命值填充
        hp_percent = player.get_health_percentage()
        hp_fill_width = int(hp_bar_width * hp_percent)
        
        # 根据生命值百分比选择颜色
        if hp_percent > 0.6:
            hp_color = self.colors['green']
        elif hp_percent > 0.3:
            hp_color = self.colors['yellow']
        else:
            hp_color = self.colors['red']
        
        pygame.draw.rect(self.screen, hp_color,
                        (hp_bar_x, hp_bar_y, hp_fill_width, hp_bar_height))
        
        # 生命值文本
        hp_text = f"HP: {player.current_health}/{player.max_health}"
        self.draw_text(hp_text, hp_bar_x + hp_bar_width // 2, hp_bar_y + hp_bar_height // 2,
                      self.colors['white'], self.font_small, center=True)
        
        # 边框
        pygame.draw.rect(self.screen, self.colors['white'],
                        (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height), 2)
        
        # 位置信息
        pos_text = f"位置: ({player.position.x:.0f}, {player.position.y:.0f})"
        self.draw_text(pos_text, 10, 60, self.colors['light_gray'], self.font_small)
        
        # 使用预创建的底部菜单提示背景（性能优化）
        self.screen.blit(self.hud_bottom_bg, (0, self.height - 40))
        
        menu_text = "按 [M] 打开菜单 | [I] 背包 | [Q] 任务 | [C] 基地 | [TAB] 小地图 | [ESC] 暂停/返回"
        self.draw_text(menu_text, 10, self.height - 30, self.colors['white'], self.font_small)
    
    def draw_menu(self, menu_items: List[Tuple[str, str]], selected_index: int = 0):
        """
        绘制菜单
        
        Args:
            menu_items: 菜单项列表 [(key, text), ...]
            selected_index: 选中的索引
        """
        # 使用预创建的半透明背景（性能优化）
        self.screen.blit(self.overlay_bg, (0, 0))
        
        # 标题
        self.draw_text("游戏菜单", self.width // 2, 100, 
                      self.colors['white'], self.font_large, center=True)
        
        # 菜单项
        start_y = 200
        spacing = 50
        
        for i, (key, text) in enumerate(menu_items):
            y = start_y + i * spacing
            color = self.colors['yellow'] if i == selected_index else self.colors['white']
            
            menu_text = f"[{key}] {text}"
            self.draw_text(menu_text, self.width // 2, y, color, self.font_medium, center=True)
    
    def draw_dialog(self, npc: NPC, messages: List[str], input_text: str = "", options: List[str] = None):
        """
        绘制对话界面（美化版）
        
        Args:
            npc: NPC对象
            messages: 消息列表
            input_text: 输入的文本
            options: 交互选项列表（如 ["[1] 交易", "[2] 离开"]）
        """
        # 对话框参数
        dialog_height = 250
        dialog_y = self.height - dialog_height - 20
        dialog_width = self.width - 40
        dialog_x = 20
        
        # 绘制半透明背景面板
        dialog_bg = pygame.Surface((dialog_width, dialog_height))
        dialog_bg.set_alpha(230)
        dialog_bg.fill(self.colors['black'])
        self.screen.blit(dialog_bg, (dialog_x, dialog_y))
        
        # 绘制白色边框
        pygame.draw.rect(self.screen, self.colors['white'], 
                        (dialog_x, dialog_y, dialog_width, dialog_height), 3)
        
        # === 左侧：NPC头像区域 ===
        avatar_x = dialog_x + 30
        avatar_y = dialog_y + 30
        avatar_size = 80
        
        # NPC头像（大号圆形图标）
        npc_faction = getattr(npc, 'faction', 'neutral')
        if npc_faction in ['enemy', 'bandit']:
            avatar_color = (200, 50, 50)  # 红色（敌对）
        elif npc_faction == 'alliance':
            avatar_color = (50, 150, 255)  # 蓝色（友善）
        else:
            avatar_color = (50, 200, 50)  # 绿色（中立）
        
        # 绘制头像阴影
        shadow_surface = pygame.Surface((avatar_size + 4, avatar_size + 4), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surface, (0, 0, 0, 150), 
                         (avatar_size // 2 + 2, avatar_size // 2 + 2), avatar_size // 2)
        self.screen.blit(shadow_surface, (avatar_x - 2, avatar_y - 2))
        
        # 绘制头像主体
        pygame.draw.circle(self.screen, avatar_color, 
                         (avatar_x + avatar_size // 2, avatar_y + avatar_size // 2), 
                         avatar_size // 2)
        pygame.draw.circle(self.screen, self.colors['white'], 
                         (avatar_x + avatar_size // 2, avatar_y + avatar_size // 2), 
                         avatar_size // 2, 2)
        
        # NPC名称（带背景）
        name_bg_height = 30
        name_bg = pygame.Surface((avatar_size + 20, name_bg_height))
        name_bg.set_alpha(200)
        name_bg.fill((50, 50, 50))
        self.screen.blit(name_bg, (avatar_x - 10, avatar_y + avatar_size + 10))
        
        self._draw_text_with_outline(npc.name, avatar_x + avatar_size // 2, 
                                    avatar_y + avatar_size + 25,
                                    self.colors['white'], self.font_small, center=True)
        
        # === 中间：对话内容区域 ===
        content_x = avatar_x + avatar_size + 40
        content_y = dialog_y + 30
        content_width = dialog_width - (content_x - dialog_x) - 30
        content_height = dialog_height - 100
        
        # 绘制对话历史（最近5条）
        y_offset = 0
        for message in messages[-5:]:
            if y_offset + 30 <= content_height:
                self._draw_text_with_outline(message, content_x, content_y + y_offset,
                                           self.colors['light_gray'], self.font_small)
                y_offset += 30
        
        # 输入框
        input_y = dialog_y + dialog_height - 50
        input_rect = pygame.Rect(content_x, input_y, content_width, 30)
        pygame.draw.rect(self.screen, self.colors['white'], input_rect, 2)
        if input_text:
            self.draw_text(input_text, content_x + 10, input_y + 15,
                          self.colors['white'], self.font_small)
        
        # === 右侧：交互选项区域 ===
        if options:
            options_x = dialog_x + dialog_width - 200
            options_y = dialog_y + 30
            
            self._draw_text_with_outline("选项:", options_x, options_y,
                                       self.colors['yellow'], self.font_small)
            
            option_y = options_y + 35
            for option in options:
                # 高亮显示选项
                option_color = self.colors['yellow'] if '[1]' in option or '[2]' in option else self.colors['light_gray']
                self._draw_text_with_outline(option, options_x, option_y,
                                           option_color, self.font_small)
                option_y += 30
    
    def draw_trade(self, player, merchant):
        """绘制交易界面"""
        # 1. 半透明背景
        self.screen.blit(self.overlay_bg, (0, 0))
        
        # 2. 绘制主窗口框
        ww, wh = 900, 600
        wx, wy = (self.width - ww) // 2, (self.height - wh) // 2
        pygame.draw.rect(self.screen, self.colors['dark_gray'], (wx, wy, ww, wh))
        pygame.draw.rect(self.screen, self.colors['white'], (wx, wy, ww, wh), 2)
        
        # 3. 标题
        m_name = merchant.name if merchant else "商人"
        self.draw_text(f"与 {m_name} 交易中", self.width // 2, wy + 20, self.colors['yellow'], self.font_large, center=True)
        
        # 4. 左右分栏
        # 左侧：玩家
        self.draw_text("【你的背包】", wx + 100, wy + 70, self.colors['white'], self.font_medium)
        self.draw_text(f"金币: {getattr(player, 'money', 0)}", wx + 100, wy + 110, self.colors['yellow'], self.font_small)
        
        # 显示玩家物品（前8个）
        y = wy + 150
        inv = getattr(player, 'inventory', {}) or {}
        idx = 1
        for item, data in list(inv.items())[:8]:
            price = int(data.get('price', 0) * 0.7)
            self.draw_text(f"[{idx}] {item} x{data.get('count',0)} (卖:{price})", wx + 40, y, self.colors['white'], self.font_small)
            y += 30
            idx += 1
            
        # 右侧：商人
        self.draw_text("【商人货物】", wx + ww - 300, wy + 70, self.colors['white'], self.font_medium)
        self.draw_text(f"资金: {getattr(merchant, 'money', 0)}", wx + ww - 300, wy + 110, self.colors['yellow'], self.font_small)
        
        # 显示商人物品（前8个）
        y = wy + 150
        m_inv = getattr(merchant, 'inventory', {}) or {}
        idx = 1
        for item, data in list(m_inv.items())[:8]:
            self.draw_text(f"[{idx}] {item} x{data.get('count',0)} (买:{data.get('price',0)})", wx + ww//2 + 40, y, self.colors['white'], self.font_small)
            y += 30
            idx += 1
        
        # 5. 底部提示
        self.draw_text("按 [1-8] 购买 | 按 [Shift+1-8] 出售 | [ESC] 离开", 
                      self.width // 2, wy + wh - 40, 
                      self.colors['light_gray'], self.font_small, center=True)
    def handle_events(self) -> List[pygame.event.Event]:
        """
        处理事件
        
        Returns:
            未处理的事件列表
        """
        events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None  # 返回None表示退出
            events.append(event)
        return events
    
    def update(self):
        """更新显示"""
        pygame.display.flip()
        self.clock.tick(self.fps)
    
    def quit(self):
        """退出窗口"""
        pygame.quit()
        self.logger.info("游戏窗口已关闭")

