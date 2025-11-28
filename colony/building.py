"""
建筑系统
定义基地中的各种建筑
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, List

from core.world import Position


class BuildingType(Enum):
    """建筑类型"""
    # 基础建筑
    WALL = "wall"                      # 墙
    DOOR = "door"                      # 门
    FLOOR = "floor"                    # 地板
    
    # 生产建筑
    WORKSHOP = "workshop"              # 工坊
    KITCHEN = "kitchen"                # 厨房
    FARM = "farm"                      # 农场
    MINE = "mine"                      # 矿场
    
    # 居住建筑
    BEDROOM = "bedroom"                # 卧室
    DORMITORY = "dormitory"            # 宿舍
    
    # 存储建筑
    WAREHOUSE = "warehouse"            # 仓库
    
    # 防御建筑
    WATCHTOWER = "watchtower"          # 瞭望塔
    GATE = "gate"                      # 大门


@dataclass
class Building:
    """建筑类"""
    building_type: BuildingType    # 建筑类型
    position: Position             # 建筑位置
    size: tuple = (1, 1)           # 建筑大小（宽度，高度）
    health: int = 100              # 建筑生命值
    max_health: int = 100          # 最大生命值
    level: int = 1                 # 建筑等级
    
    # 建筑功能相关
    production_rate: float = 0.0   # 生产效率（如果可生产）
    storage_capacity: Dict = field(default_factory=dict)  # 存储容量
    
    # 建筑状态
    is_completed: bool = False     # 是否建造完成
    is_destroyed: bool = False     # 是否被摧毁
    
    def __post_init__(self):
        """初始化后处理"""
        # 根据建筑类型设置默认属性
        if self.building_type == BuildingType.WAREHOUSE:
            # 仓库有存储容量
            self.storage_capacity = {
                "food": 1000,
                "wood": 500,
                "stone": 500,
                "metal": 500
            }
        elif self.building_type == BuildingType.FARM:
            self.production_rate = 10.0  # 每小时生产10单位食物
        elif self.building_type == BuildingType.MINE:
            self.production_rate = 5.0   # 每小时生产5单位金属
    
    def take_damage(self, damage: int):
        """
        建筑受到伤害
        
        Args:
            damage: 伤害值
        """
        self.health = max(0, self.health - damage)
        if self.health <= 0:
            self.is_destroyed = True
            self.is_completed = False
    
    def repair(self, amount: int):
        """
        修理建筑
        
        Args:
            amount: 修理量
        """
        if self.is_destroyed:
            return
        self.health = min(self.max_health, self.health + amount)
    
    def upgrade(self):
        """升级建筑"""
        if not self.is_completed or self.is_destroyed:
            return
        
        self.level += 1
        old_max_health = self.max_health
        self.max_health = int(self.max_health * 1.2)
        self.health += (self.max_health - old_max_health)
        self.production_rate *= 1.15  # 生产效率提升15%
    
    def complete(self):
        """完成建造"""
        self.is_completed = True
        self.health = self.max_health
    
    def get_efficiency(self) -> float:
        """
        获取建筑效率（基于生命值和等级）
        
        Returns:
            效率值（0.0-1.0）
        """
        if not self.is_completed or self.is_destroyed:
            return 0.0
        
        health_ratio = self.health / self.max_health
        level_bonus = 1.0 + (self.level - 1) * 0.1
        return min(1.0, health_ratio * level_bonus)


class BuildingManager:
    """建筑管理器"""
    
    def __init__(self):
        """初始化建筑管理器"""
        self.buildings: List[Building] = []
    
    def add_building(self, building: Building):
        """
        添加建筑
        
        Args:
            building: 建筑对象
        """
        self.buildings.append(building)
    
    def remove_building(self, building: Building):
        """
        移除建筑
        
        Args:
            building: 建筑对象
        """
        if building in self.buildings:
            self.buildings.remove(building)
    
    def get_buildings_at(self, position: Position, radius: float = 10.0) -> List[Building]:
        """
        获取指定位置的建筑
        
        Args:
            position: 位置
            radius: 搜索半径
            
        Returns:
            建筑列表
        """
        result = []
        for building in self.buildings:
            distance = building.position.distance_to(position)
            if distance <= radius:
                result.append(building)
        return result
    
    def get_buildings_by_type(self, building_type: BuildingType) -> List[Building]:
        """
        获取指定类型的建筑
        
        Args:
            building_type: 建筑类型
            
        Returns:
            建筑列表
        """
        return [
            building for building in self.buildings
            if building.building_type == building_type and building.is_completed
        ]
    
    def can_build_at(self, position: Position, size: tuple) -> bool:
        """
        检查是否可以在指定位置建造（检查是否有冲突）
        
        Args:
            position: 建造位置
            size: 建筑大小
            
        Returns:
            是否可以建造
        """
        # 简化处理：检查是否有其他建筑在附近
        for building in self.buildings:
            distance = building.position.distance_to(position)
            if distance < 50.0:  # 最小建造距离
                return False
        return True
    
    def get_total_production(self, resource_type: str) -> float:
        """
        获取指定资源的总生产速度
        
        Args:
            resource_type: 资源类型名称
            
        Returns:
            总生产速度
        """
        total = 0.0
        for building in self.buildings:
            if building.is_completed and not building.is_destroyed:
                # 这里可以根据建筑类型判断生产什么资源
                if building_type_produces(building.building_type, resource_type):
                    total += building.production_rate * building.get_efficiency()
        return total


def building_type_produces(building_type: BuildingType, resource_type: str) -> bool:
    """
    判断建筑类型是否生产指定资源
    
    Args:
        building_type: 建筑类型
        resource_type: 资源类型
        
    Returns:
        是否生产该资源
    """
    production_map = {
        BuildingType.FARM: ["food"],
        BuildingType.MINE: ["metal", "stone"],
    }
    
    return resource_type in production_map.get(building_type, [])


# 建筑成本定义
BUILDING_COSTS = {
    BuildingType.WALL: {"wood": 10, "stone": 5},
    BuildingType.DOOR: {"wood": 5},
    BuildingType.WORKSHOP: {"wood": 50, "stone": 20},
    BuildingType.KITCHEN: {"wood": 30, "stone": 10},
    BuildingType.FARM: {"wood": 20},
    BuildingType.MINE: {"wood": 40, "metal": 10},
    BuildingType.BEDROOM: {"wood": 40},
    BuildingType.WAREHOUSE: {"wood": 60, "stone": 30},
    BuildingType.WATCHTOWER: {"wood": 30, "stone": 40},
}

