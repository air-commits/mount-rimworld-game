"""
世界系统模块
====================
定义游戏世界、地形类型和位置

【设计说明】
- 所有地图都是纯草地，铺满整个地图
- 没有障碍物，没有空气墙
- 玩家可以在任何位置自由移动
"""

from dataclasses import dataclass
from enum import Enum
from typing import List
from utils.logger import get_logger


class TerrainType(Enum):
    """
    地形类型枚举类
    ====================
    目前只使用GRASS（草地），所有地图都是草地
    """
    GRASS = "grass"  # 草地（唯一使用的地形）


@dataclass
class Position:
    """
    位置坐标类
    ====================
    表示游戏世界中的一个二维坐标点
    
    【属性说明】
    - x: X坐标（浮点数，单位：像素）
    - y: Y坐标（浮点数，单位：像素）
    """
    x: float  # X坐标（像素）
    y: float  # Y坐标（像素）
    
    def distance_to(self, other: 'Position') -> float:
        """
        计算到另一个位置的距离
        
        【功能说明】
        使用欧几里得距离公式计算两点之间的距离
        公式：√[(x1-x2)² + (y1-y2)²]
        
        【参数说明】
        - other: 另一个位置对象（Position类型）
        
        【返回值】
        - float: 两点之间的距离（像素）
        """
        # 计算X轴和Y轴的差值
        dx = self.x - other.x  # X轴距离差
        dy = self.y - other.y  # Y轴距离差
        
        # 使用勾股定理计算直线距离
        return (dx ** 2 + dy ** 2) ** 0.5


class World:
    """
    游戏世界类
    ====================
    管理整个游戏世界，包括：
    1. 世界尺寸（宽度、高度）
    2. 地形网格（每个格子都是草地）
    3. 位置验证和移动检测
    
    【核心概念】
    - 世界被分成一个个小格子（瓦片），每个格子都是草地
    - 例如：1000x1000像素的世界，32像素的瓦片 = 31x31个格子
    - 所有格子都是草地，玩家可以在任何位置自由移动
    """
    
    def __init__(self, width: int = 1000, height: int = 1000, tile_size: int = 32):
        """
        初始化游戏世界
        
        【功能说明】
        创建一个新的游戏世界，所有地形都是草地
        
        【参数说明】
        - width: 世界宽度（像素），默认1000
        - height: 世界高度（像素），默认1000
        - tile_size: 每个瓦片的大小（像素），默认32
        """
        # 初始化日志记录器
        self.logger = get_logger("World")
        
        # 保存世界基本信息
        self.width = width      # 世界宽度（像素）
        self.height = height    # 世界高度（像素）
        self.tile_size = tile_size  # 每个瓦片的大小（像素）
        
        # 计算网格大小
        # 网格 = 世界尺寸 ÷ 瓦片大小
        grid_width = width // tile_size   # 横向有多少个格子
        grid_height = height // tile_size  # 纵向有多少个格子
        
        # 地形生成逻辑：所有格子都是草地
        # 创建二维数组：terrain_grid[y][x] = 第y行第x列的地形类型
        self.terrain_grid: List[List[TerrainType]] = []
        
        # 遍历每一行，全部填充为草地
        for y in range(grid_height):
            row = []  # 创建一行
            # 遍历这一行的每一列，全部设置为草地
            for x in range(grid_width):
                row.append(TerrainType.GRASS)  # 全部为草地
            # 把这一行添加到网格中
            self.terrain_grid.append(row)
        
        # 记录日志
        self.logger.info(
            f"[世界] 创建世界 - 尺寸: {width}x{height}, "
            f"瓦片大小: {tile_size}, 网格: {grid_width}x{grid_height}, "
            f"全部为草地"
        )
    
    def is_valid_position(self, position: Position) -> bool:
        """
        检查位置是否在世界范围内
        
        【功能说明】
        判断一个坐标点是否在世界地图的边界内
        
        【参数说明】
        - position: 要检查的位置坐标（Position对象）
        
        【返回值】
        - bool: True表示位置有效（在世界内），False表示位置无效（超出边界）
        """
        # 检查X坐标：必须在 [0, width) 范围内
        x_valid = 0 <= position.x < self.width
        # 检查Y坐标：必须在 [0, height) 范围内
        y_valid = 0 <= position.y < self.height
        # 两个坐标都有效，位置才有效
        return x_valid and y_valid
    
    def get_terrain_at(self, position: Position) -> TerrainType:
        """
        获取指定位置的地形类型
        
        【功能说明】
        根据世界坐标（像素），找到对应的格子，返回该格子的地形类型
        
        【参数说明】
        - position: 世界坐标（Position对象，单位：像素）
        
        【返回值】
        - TerrainType: 该位置的地形类型（当前总是GRASS）
        """
        # 检查位置是否有效
        if not self.is_valid_position(position):
            return TerrainType.GRASS
        
        # 将像素坐标转换为格子坐标
        grid_x = int(position.x // self.tile_size)  # 列索引
        grid_y = int(position.y // self.tile_size)  # 行索引
        
        # 从地形网格中获取地形类型
        if (grid_y < len(self.terrain_grid) and 
            grid_x < len(self.terrain_grid[0])):
            return self.terrain_grid[grid_y][grid_x]
        
        # 如果超出网格范围，返回默认值（草地）
        return TerrainType.GRASS
    
    def can_move_to(self, position: Position) -> bool:
        """
        检查是否可以移动到指定位置
        
        【功能说明】
        判断玩家是否可以移动到目标位置
        当前所有地形都是草地，所以只要在世界范围内就可以移动
        
        【参数说明】
        - position: 目标位置（Position对象，单位：像素）
        
        【返回值】
        - bool: True表示可以移动，False表示超出边界
        """
        # 检查位置是否在世界范围内
        # 所有地形都是草地，都可以通行，只需要检查边界
        return self.is_valid_position(position)

