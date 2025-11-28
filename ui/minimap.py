"""
小地图系统
显示世界的小地图视图
"""

import pygame
from typing import List, Tuple
from core.world import Position, TerrainType
from entities.player import Player
from entities.npc import NPC


class Minimap:
    """小地图"""
    
    def __init__(self, width: int = 200, height: int = 200, world_width: int = 1000, world_height: int = 1000):
        """
        初始化小地图
        
        Args:
            width: 小地图宽度（像素）
            height: 小地图高度（像素）
            world_width: 世界宽度
            world_height: 世界高度
        """
        self.width = width
        self.height = height
        self.world_width = world_width
        self.world_height = world_height
        
        # 小地图位置（右上角）
        self.x = 0  # 将在渲染时计算
        self.y = 0
        
        # 颜色
        self.colors = {
            'bg': (40, 40, 40),
            'border': (200, 200, 200),
            'player': (0, 100, 255),
            'npc': (0, 255, 0),
            'grass': (34, 139, 34),
            'forest': (0, 100, 0),
            'water': (0, 119, 190),
            'mountain': (105, 105, 105),
        }
        
        # 是否显示
        self.visible = True
    
    def world_to_minimap(self, world_pos: Position) -> Tuple[int, int]:
        """
        将世界坐标转换为小地图坐标
        
        Args:
            world_pos: 世界坐标
            
        Returns:
            小地图坐标 (x, y)
        """
        # 防止除以零
        safe_world_width = self.world_width if self.world_width > 0 else 1
        safe_world_height = self.world_height if self.world_height > 0 else 1
        
        x = int((world_pos.x / safe_world_width) * self.width)
        y = int((world_pos.y / safe_world_height) * self.height)
        return x, y
    
    def draw(self, screen: pygame.Surface, screen_width: int, screen_height: int,
             world, player: Player, entities: List):
        """
        绘制小地图
        
        Args:
            screen: 屏幕表面
            screen_width: 屏幕宽度
            screen_height: 屏幕高度
            world: 世界对象
            player: 玩家对象
            entities: 实体列表
        """
        if not self.visible:
            return
        
        # === 修复：更新世界尺寸，确保坐标转换正确 ===
        if hasattr(world, 'width') and hasattr(world, 'height'):
            self.world_width = world.width
            self.world_height = world.height
        
        # 计算小地图位置（右上角，留出边距）
        margin = 10
        self.x = screen_width - self.width - margin
        self.y = margin
        
        # 创建小地图表面
        minimap_surface = pygame.Surface((self.width, self.height))
        minimap_surface.fill(self.colors['bg'])
        
        # 绘制地形（简化，只显示主要地形类型）
        # 这里可以优化为只显示重要区域
        if hasattr(world, 'terrain_grid'):
            grid_width = len(world.terrain_grid[0]) if world.terrain_grid else 0
            grid_height = len(world.terrain_grid) if world.terrain_grid else 0
            
            # 采样绘制（为了性能，不绘制所有瓦片）
            sample_rate = max(1, max(grid_width, grid_height) // 50)
            
            for y in range(0, grid_height, sample_rate):
                for x in range(0, grid_width, sample_rate):
                    if y < len(world.terrain_grid) and x < len(world.terrain_grid[0]):
                        terrain = world.terrain_grid[y][x]
                        
                        # 选择颜色
                        if terrain == TerrainType.GRASS:
                            color = self.colors['grass']
                        elif terrain == TerrainType.FOREST:
                            color = self.colors['forest']
                        elif terrain == TerrainType.WATER:
                            color = self.colors['water']
                        elif terrain == TerrainType.MOUNTAIN:
                            color = self.colors['mountain']
                        else:
                            color = (50, 50, 50)
                        
                        # 计算像素位置
                        px = int((x / grid_width) * self.width)
                        py = int((y / grid_height) * self.height)
                        size = max(1, int(self.width / (grid_width / sample_rate))) + 1
                        
                        pygame.draw.rect(minimap_surface, color,
                                       (px, py, size, size))
        
        # 绘制实体
        for entity in entities:
            if not entity.is_alive:
                continue
            
            mx, my = self.world_to_minimap(entity.position)
            
            # 确保点在小地图范围内
            if 0 <= mx <= self.width and 0 <= my <= self.height:
                if isinstance(entity, Player):
                    pygame.draw.circle(minimap_surface, self.colors['player'],
                                     (mx, my), 3)
                elif isinstance(entity, NPC):
                    pygame.draw.circle(minimap_surface, self.colors['npc'],
                                     (mx, my), 2)
        
        # 绘制边框
        pygame.draw.rect(minimap_surface, self.colors['border'],
                        (0, 0, self.width, self.height), 2)
        
        # 绘制标题
        try:
            font = pygame.font.Font(None, 20)
            title = font.render("小地图", True, (255, 255, 255))
            minimap_surface.blit(title, (5, 5))
        except:
            pass
        
        # 绘制到屏幕
        screen.blit(minimap_surface, (self.x, self.y))
    
    def toggle(self):
        """切换显示状态"""
        self.visible = not self.visible


