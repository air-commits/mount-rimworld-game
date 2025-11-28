"""
世界系统
管理游戏世界的地图、位置、地形等
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum
import random


class TerrainType(Enum):
    """地形类型"""
    GRASS = "grass"          # 草地
    FOREST = "forest"        # 森林
    MOUNTAIN = "mountain"    # 山地
    WATER = "water"          # 水域
    DESERT = "desert"        # 沙漠
    ROAD = "road"            # 道路


@dataclass
class Position:
    """位置坐标"""
    x: float
    y: float
    
    def distance_to(self, other: 'Position') -> float:
        """
        计算到另一个位置的距离
        
        Args:
            other: 目标位置
            
        Returns:
            距离
        """
        dx = self.x - other.x
        dy = self.y - other.y
        return (dx ** 2 + dy ** 2) ** 0.5
    
    def distance_sq_to(self, other: 'Position') -> float:
        """
        计算到另一个位置的平方距离（性能优化，避免开方）
        
        Args:
            other: 目标位置
            
        Returns:
            平方距离
        """
        dx = self.x - other.x
        dy = self.y - other.y
        return dx ** 2 + dy ** 2
    
    def __add__(self, other: 'Position') -> 'Position':
        """位置相加"""
        return Position(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Position') -> 'Position':
        """位置相减"""
        return Position(self.x - other.x, self.y - other.y)


class World:
    """游戏世界"""
    
    def __init__(self, width: int = 1000, height: int = 1000, tile_size: int = 32):
        """
        初始化游戏世界
        
        Args:
            width: 世界宽度
            height: 世界高度
            tile_size: 瓦片大小
        """
        self.width = width
        self.height = height
        self.tile_size = tile_size
        
        # 地形网格（每个瓦片的地形类型）- 用于局部地图详细地形
        self.terrain_grid: List[List[TerrainType]] = []
        
        # 大地图简略地形网格（用于世界地图显示，分辨率较低）
        self.global_map_grid: List[List[TerrainType]] = []
        self.global_map_tile_size = 64  # 大地图每个瓦片代表64像素
        
        # 初始化地形
        self._generate_terrain()
        
        # 初始化大地图地形
        self._generate_global_map()
    
    def _generate_terrain(self):
        """
        生成世界地形（性能优化版本）
        使用平方距离比较，避免开方运算
        """
        # 计算网格大小
        grid_width = self.width // self.tile_size
        grid_height = self.height // self.tile_size
        
        # 初始化地形网格（默认为草地）
        self.terrain_grid = [
            [TerrainType.GRASS for _ in range(grid_width)]
            for _ in range(grid_height)
        ]
        
        # 性能优化：预计算中心点和最大距离的平方（避免在循环内重复计算）
        center_x, center_y = grid_width / 2, grid_height / 2
        max_dist_sq = center_x ** 2 + center_y ** 2  # 最大距离的平方
        
        # 简单的地形生成算法（优化：使用平方距离比较）
        for y in range(grid_height):
            for x in range(grid_width):
                # 根据位置生成不同地形
                rand = random.random()
                
                # 性能优化：使用平方距离比较，避免开方运算
                dx = x - center_x
                dy = y - center_y
                dist_sq = dx ** 2 + dy ** 2  # 平方距离
                
                # 使用平方距离比例（dist_sq / max_dist_sq）代替 (dist / max_dist)
                dist_ratio_sq = dist_sq / max_dist_sq if max_dist_sq > 0 else 0
                
                if rand < 0.1:
                    self.terrain_grid[y][x] = TerrainType.WATER
                elif rand < 0.3:
                    self.terrain_grid[y][x] = TerrainType.FOREST
                elif dist_ratio_sq > 0.64:  # 0.8^2 = 0.64，避免开方
                    self.terrain_grid[y][x] = TerrainType.MOUNTAIN
                elif rand < 0.05:
                    self.terrain_grid[y][x] = TerrainType.DESERT
    
    def _generate_global_map(self):
        """
        生成大地图简略地形（用于世界地图显示）
        使用较低分辨率生成，看起来像大陆地形
        """
        # 计算大地图网格大小（较低分辨率）
        global_grid_width = max(1, self.width // self.global_map_tile_size)
        global_grid_height = max(1, self.height // self.global_map_tile_size)
        
        # 初始化大地图网格（默认为草地）
        self.global_map_grid = [
            [TerrainType.GRASS for _ in range(global_grid_width)]
            for _ in range(global_grid_height)
        ]
        
        # 使用简单的噪声生成类似大陆的地形
        center_x, center_y = global_grid_width / 2, global_grid_height / 2
        max_dist_sq = (center_x ** 2 + center_y ** 2) if (center_x ** 2 + center_y ** 2) > 0 else 1
        
        # 设置随机种子以获得一致的地形
        random.seed(42)  # 固定种子，确保每次生成相同的地形
        
        for y in range(global_grid_height):
            for x in range(global_grid_width):
                # 计算到中心的距离（用于生成中心为陆地，边缘为水域的地形）
                dx = x - center_x
                dy = y - center_y
                dist_sq = dx ** 2 + dy ** 2
                dist_ratio = dist_sq / max_dist_sq
                
                # 使用噪声函数（简化版）
                noise_x = x / max(global_grid_width, 1) * 3.0
                noise_y = y / max(global_grid_height, 1) * 3.0
                noise_value = (random.random() + random.random() + random.random()) / 3.0
                
                # 地形生成规则
                if dist_ratio > 0.85:  # 边缘区域：水域
                    self.global_map_grid[y][x] = TerrainType.WATER
                elif dist_ratio > 0.70:  # 外围区域：混合（20%水域）
                    if random.random() < 0.2:
                        self.global_map_grid[y][x] = TerrainType.WATER
                    else:
                        self.global_map_grid[y][x] = TerrainType.GRASS
                elif noise_value < 0.15:  # 低洼地区：水域（形成河流/湖泊）
                    self.global_map_grid[y][x] = TerrainType.WATER
                elif noise_value > 0.85:  # 高地区域：山脉
                    self.global_map_grid[y][x] = TerrainType.MOUNTAIN
                elif noise_value > 0.70:  # 中等高度：森林
                    self.global_map_grid[y][x] = TerrainType.FOREST
                else:
                    # 大部分区域是草地
                    self.global_map_grid[y][x] = TerrainType.GRASS
        
        # 恢复随机种子
        random.seed()
    
    def get_global_terrain_at(self, position: Position) -> TerrainType:
        """
        获取大地图指定位置的简略地形类型
        
        Args:
            position: 位置坐标
            
        Returns:
            地形类型
        """
        if not self.global_map_grid:
            return TerrainType.GRASS
        
        grid_x = int(position.x // self.global_map_tile_size)
        grid_y = int(position.y // self.global_map_tile_size)
        
        # 边界检查
        grid_height = len(self.global_map_grid)
        grid_width = len(self.global_map_grid[0]) if grid_height > 0 else 0
        
        if 0 <= grid_y < grid_height and 0 <= grid_x < grid_width:
            return self.global_map_grid[grid_y][grid_x]
        return TerrainType.GRASS
    
    def get_terrain_at(self, position: Position) -> TerrainType:
        """
        获取指定位置的地形类型
        
        Args:
            position: 位置坐标
            
        Returns:
            地形类型
        """
        if not self.is_valid_position(position):
            return TerrainType.GRASS
        
        grid_x = int(position.x // self.tile_size)
        grid_y = int(position.y // self.tile_size)
        
        # 边界检查
        grid_height = len(self.terrain_grid)
        grid_width = len(self.terrain_grid[0]) if grid_height > 0 else 0
        
        if 0 <= grid_y < grid_height and 0 <= grid_x < grid_width:
            return self.terrain_grid[grid_y][grid_x]
        return TerrainType.GRASS
    
    def is_valid_position(self, position: Position) -> bool:
        """
        检查位置是否在世界范围内
        
        Args:
            position: 位置坐标
            
        Returns:
            是否有效
        """
        return 0 <= position.x < self.width and 0 <= position.y < self.height
    
    def can_move_to(self, position: Position) -> bool:
        """
        检查是否可以移动到指定位置（考虑地形）
        
        Args:
            position: 目标位置
            
        Returns:
            是否可以移动
        """
        if not self.is_valid_position(position):
            return False
        
        terrain = self.get_terrain_at(position)
        # 水域不能直接移动
        return terrain != TerrainType.WATER
    
    def get_random_position(self) -> Position:
        """
        获取世界内的随机位置
        
        Returns:
            随机位置
        """
        return Position(
            random.uniform(0, self.width),
            random.uniform(0, self.height)
        )

