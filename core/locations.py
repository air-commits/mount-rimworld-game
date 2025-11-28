"""
地点系统
定义大地图上的据点（城镇、村庄、资源点等）
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import random

from core.world import Position, World
from utils.logger import get_logger


class LocationType(Enum):
    """地点类型"""
    TOWN = "town"                    # 城镇
    VILLAGE = "village"              # 村庄
    RESOURCE_POINT = "resource_point"  # 资源点
    DUNGEON = "dungeon"              # 地牢
    FORTRESS = "fortress"            # 要塞
    MARKET = "market"                # 市场


@dataclass
class Location:
    """大地图上的地点"""
    
    name: str                        # 地点名称
    position: Position               # 在大地图的坐标
    location_type: LocationType      # 地点类型
    faction: str = "neutral"         # 所属势力
    
    # 地点属性
    population: int = 0              # 人口数量（城镇/村庄）
    prosperity: int = 50             # 繁荣度（0-100）
    
    # 资源点属性
    resource_type: Optional[str] = None  # 资源类型（如果是资源点）
    resource_amount: int = 100       # 资源数量
    
    # 内部地图数据
    local_map: Optional[World] = None  # 局部地图（环世界风格）
    local_npcs: List = field(default_factory=list)  # 局部地图的NPC列表
    
    # 其他属性
    metadata: Dict[str, Any] = field(default_factory=dict)  # 其他元数据
    
    def __post_init__(self):
        """初始化后处理"""
        self.logger = get_logger(f"Location_{self.name}")
        
        # 根据类型设置默认值
        if self.location_type == LocationType.TOWN:
            if self.population == 0:
                self.population = 500  # 默认城镇人口
        elif self.location_type == LocationType.VILLAGE:
            if self.population == 0:
                self.population = 50   # 默认村庄人口
    
    def enter(self) -> Dict[str, Any]:
        """
        进入地点
        
        Returns:
            进入地点后的场景数据
        """
        self.logger.info(f"进入地点: {self.name} ({self.location_type.value})")
        
        # 如果还没有生成局部地图，现在生成
        if self.local_map is None:
            self.local_map = self.generate_local_map()
        
        return {
            "location": self,
            "local_map": self.local_map,
            "description": self.get_description(),
            "npcs": self.local_npcs  # === 🔴 修复：返回本地NPC列表 ===
        }
    
    def generate_local_map(self) -> World:
        """
        生成该地点内部的环世界风格地图
        
        Returns:
            World对象，代表局部地图
        """
        self.logger.debug(f"为 {self.name} 生成局部地图...")
        
        # 根据地点类型生成不同大小的地图
        width, height = self._get_map_size()
        
        # 创建局部地图世界
        local_world = World(width=width, height=height, tile_size=32)
        
        # 根据地点类型生成不同的地形和建筑
        if self.location_type == LocationType.TOWN:
            self._generate_town_map(local_world)
        elif self.location_type == LocationType.VILLAGE:
            self._generate_village_map(local_world)
        elif self.location_type == LocationType.RESOURCE_POINT:
            self._generate_resource_point_map(local_world)
        elif self.location_type == LocationType.DUNGEON:
            self._generate_dungeon_map(local_world)
        else:
            # 默认生成基础地形
            self._generate_default_map(local_world)
        
        # === 🔴 修复：生成本地NPC（如果还没有生成） ===
        if not self.local_npcs:
            self._generate_local_npcs(local_world)
        
        return local_world
    
    def _generate_local_npcs(self, world: World):
        """
        生成本地NPC（村民、市民、守卫等）
        
        Args:
            world: 局部地图世界对象
        """
        # 延迟导入，避免循环依赖
        from entities.npc import NPC, NPCPersonality
        
        self.logger.debug(f"为 {self.name} 生成本地NPC...")
        
        if self.location_type == LocationType.VILLAGE:
            # 村庄：生成3-5个村民
            npc_count = random.randint(3, 5)
            for i in range(npc_count):
                # 随机位置（避免在边缘）
                pos = Position(
                    random.uniform(100, world.width - 100),
                    random.uniform(100, world.height - 100)
                )
                
                # 村民名称
                villager_names = ["村民", "农夫", "渔夫", "木匠", "铁匠", "商人", "学者"]
                name = f"{random.choice(villager_names)}{i+1}"
                
                npc = NPC(
                    name=name,
                    position=pos,
                    personality=NPCPersonality(
                        traits=["kind", "helpful"],
                        kindness=random.randint(50, 80),
                        profession="villager"
                    )
                )
                npc.faction = "neutral"
                npc.is_world_entity = False  # 关键：标记为局部地图NPC
                self.local_npcs.append(npc)
        
        elif self.location_type == LocationType.TOWN:
            # 城镇：生成5-8个市民和2-3个守卫
            citizen_count = random.randint(5, 8)
            guard_count = random.randint(2, 3)
            
            # 生成市民
            citizen_names = ["市民", "商人", "工匠", "学者", "贵族", "旅行者", "小贩"]
            for i in range(citizen_count):
                pos = Position(
                    random.uniform(100, world.width - 100),
                    random.uniform(100, world.height - 100)
                )
                name = f"{random.choice(citizen_names)}{i+1}"
                
                npc = NPC(
                    name=name,
                    position=pos,
                    personality=NPCPersonality(
                        traits=["clever", "greedy"],
                        kindness=random.randint(40, 70),
                        profession="citizen"
                    )
                )
                npc.faction = "neutral"
                npc.is_world_entity = False  # 关键：标记为局部地图NPC
                self.local_npcs.append(npc)
            
            # 生成守卫
            guard_names = ["守卫", "卫兵", "哨兵", "巡逻兵"]
            for i in range(guard_count):
                pos = Position(
                    random.uniform(100, world.width - 100),
                    random.uniform(100, world.height - 100)
                )
                name = f"{random.choice(guard_names)}{i+1}"
                
                npc = NPC(
                    name=name,
                    position=pos,
                    personality=NPCPersonality(
                        traits=["brave", "loyal"],
                        aggression=random.randint(50, 70),
                        loyalty=random.randint(70, 95),
                        profession="guard"
                    )
                )
                npc.faction = "alliance"
                npc.is_world_entity = False  # 关键：标记为局部地图NPC
                self.local_npcs.append(npc)
        
        self.logger.info(f"为 {self.name} 生成了 {len(self.local_npcs)} 个本地NPC")
    
    def _get_map_size(self) -> tuple:
        """根据地点类型返回地图大小"""
        size_map = {
            LocationType.TOWN: (2000, 2000),          # 城镇较大
            LocationType.VILLAGE: (1000, 1000),       # 村庄中等
            LocationType.RESOURCE_POINT: (800, 800),  # 资源点较小
            LocationType.DUNGEON: (1500, 1500),       # 地牢中等
            LocationType.FORTRESS: (1200, 1200),      # 要塞中等
            LocationType.MARKET: (600, 600),          # 市场较小
        }
        return size_map.get(self.location_type, (1000, 1000))
    
    def _generate_town_map(self, world: World):
        """生成城镇地图（包含建筑、街道等）"""
        # 城镇地图会在中心区域生成一些建筑物
        # 这里先使用基础地形，后续可以扩展
        pass
    
    def _generate_village_map(self, world: World):
        """生成村庄地图（包含房屋、田地等）"""
        # 村庄地图会在中心生成几座房屋，周围是田地
        # 这里先使用基础地形，后续可以扩展
        pass
    
    def _generate_resource_point_map(self, world: World):
        """生成资源点地图（采矿点、伐木场等）"""
        # 资源点通常是简单的采集区域
        pass
    
    def _generate_dungeon_map(self, world: World):
        """生成地牢地图（战斗区域）"""
        # 地牢通常是战斗区域，包含敌人和宝箱
        pass
    
    def _generate_default_map(self, world: World):
        """生成默认地图（基础地形）"""
        # 使用世界的基础地形生成
        pass
    
    def get_description(self) -> str:
        """
        获取地点描述
        
        Returns:
            地点描述文本
        """
        descriptions = {
            LocationType.TOWN: f"繁荣的城镇 {self.name}，人口约 {self.population} 人。",
            LocationType.VILLAGE: f"宁静的村庄 {self.name}，人口约 {self.population} 人。",
            LocationType.RESOURCE_POINT: f"资源点 {self.name}，可以采集 {self.resource_type}。",
            LocationType.DUNGEON: f"危险的地牢 {self.name}，里面可能藏有宝藏和敌人。",
            LocationType.FORTRESS: f"坚固的要塞 {self.name}，由 {self.faction} 控制。",
            LocationType.MARKET: f"繁忙的市场 {self.name}，可以买卖商品。",
        }
        return descriptions.get(self.location_type, f"地点 {self.name}。")
    
    def distance_to(self, position: Position) -> float:
        """
        计算到另一个位置的距离
        
        Args:
            position: 目标位置
            
        Returns:
            距离
        """
        return self.position.distance_to(position)
    
    def is_enterable(self) -> bool:
        """
        检查是否可以进入该地点
        
        Returns:
            是否可以进入
        """
        # 可以根据势力关系、条件等判断
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取地点信息
        
        Returns:
            地点信息字典
        """
        return {
            "name": self.name,
            "type": self.location_type.value,
            "faction": self.faction,
            "population": self.population,
            "prosperity": self.prosperity,
            "description": self.get_description()
        }


class LocationManager:
    """地点管理器（管理所有大地图上的地点）"""
    
    def __init__(self):
        """初始化地点管理器"""
        self.locations: List[Location] = []
        self.logger = get_logger("LocationManager")
    
    def add_location(self, location: Location):
        """
        添加地点
        
        Args:
            location: 地点对象
        """
        self.locations.append(location)
        self.logger.debug(f"添加地点: {location.name} 在 ({location.position.x}, {location.position.y})")
    
    def remove_location(self, location: Location):
        """
        移除地点
        
        Args:
            location: 地点对象
        """
        if location in self.locations:
            self.locations.remove(location)
            self.logger.debug(f"移除地点: {location.name}")
    
    def get_location_at(self, position: Position, radius: float = 50.0) -> Optional[Location]:
        """
        获取指定位置附近的地点
        
        Args:
            position: 位置坐标
            radius: 搜索半径
            
        Returns:
            找到的地点，如果未找到则返回None
        """
        for location in self.locations:
            if location.distance_to(position) <= radius:
                return location
        return None
    
    def get_locations_by_type(self, location_type: LocationType) -> List[Location]:
        """
        根据类型获取地点列表
        
        Args:
            location_type: 地点类型
            
        Returns:
            地点列表
        """
        return [loc for loc in self.locations if loc.location_type == location_type]
    
    def get_all_locations(self) -> List[Location]:
        """
        获取所有地点
        
        Returns:
            地点列表
        """
        return self.locations.copy()

