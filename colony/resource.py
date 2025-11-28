"""
资源管理系统
管理游戏中的各种资源
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class ResourceType(Enum):
    """资源类型"""
    FOOD = "food"              # 食物
    WOOD = "wood"              # 木材
    STONE = "stone"            # 石头
    METAL = "metal"            # 金属
    CLOTH = "cloth"            # 布料
    LEATHER = "leather"        # 皮革
    GOLD = "gold"              # 金币


@dataclass
class Resource:
    """资源类"""
    resource_type: ResourceType    # 资源类型
    amount: float = 0.0            # 资源数量
    
    def add(self, amount: float):
        """
        增加资源
        
        Args:
            amount: 增加量
        """
        self.amount = max(0, self.amount + amount)
    
    def remove(self, amount: float) -> bool:
        """
        移除资源（如果足够）
        
        Args:
            amount: 移除量
            
        Returns:
            是否成功移除
        """
        if self.amount >= amount:
            self.amount -= amount
            return True
        return False
    
    def has_enough(self, amount: float) -> bool:
        """
        检查是否有足够的资源
        
        Args:
            amount: 需要的数量
            
        Returns:
            是否足够
        """
        return self.amount >= amount


class ResourceManager:
    """资源管理器"""
    
    def __init__(self, initial_resources: Dict[ResourceType, float] = None):
        """
        初始化资源管理器
        
        Args:
            initial_resources: 初始资源字典
        """
        self.resources: Dict[ResourceType, Resource] = {}
        
        # 初始化所有资源类型
        for resource_type in ResourceType:
            initial_amount = 0.0
            if initial_resources and resource_type in initial_resources:
                initial_amount = initial_resources[resource_type]
            self.resources[resource_type] = Resource(
                resource_type=resource_type,
                amount=initial_amount
            )
    
    def get_resource(self, resource_type: ResourceType) -> Resource:
        """
        获取指定资源
        
        Args:
            resource_type: 资源类型
            
        Returns:
            资源对象
        """
        return self.resources.get(resource_type)
    
    def get_amount(self, resource_type: ResourceType) -> float:
        """
        获取资源数量
        
        Args:
            resource_type: 资源类型
            
        Returns:
            资源数量
        """
        resource = self.get_resource(resource_type)
        return resource.amount if resource else 0.0
    
    def add_resource(self, resource_type: ResourceType, amount: float):
        """
        增加资源
        
        Args:
            resource_type: 资源类型
            amount: 增加量
        """
        resource = self.get_resource(resource_type)
        if resource:
            resource.add(amount)
    
    def remove_resource(self, resource_type: ResourceType, amount: float) -> bool:
        """
        移除资源
        
        Args:
            resource_type: 资源类型
            amount: 移除量
            
        Returns:
            是否成功移除
        """
        resource = self.get_resource(resource_type)
        if resource:
            return resource.remove(amount)
        return False
    
    def has_resources(self, required: Dict[ResourceType, float]) -> bool:
        """
        检查是否拥有足够的资源
        
        Args:
            required: 需要的资源字典
            
        Returns:
            是否足够
        """
        for resource_type, amount in required.items():
            if not self.has_enough(resource_type, amount):
                return False
        return True
    
    def has_enough(self, resource_type: ResourceType, amount: float) -> bool:
        """
        检查是否有足够的指定资源
        
        Args:
            resource_type: 资源类型
            amount: 需要的数量
            
        Returns:
            是否足够
        """
        resource = self.get_resource(resource_type)
        return resource.has_enough(amount) if resource else False
    
    def get_all_resources(self) -> Dict[ResourceType, float]:
        """
        获取所有资源数量
        
        Returns:
            资源字典
        """
        return {
            resource_type: resource.amount
            for resource_type, resource in self.resources.items()
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        lines = ["资源清单:"]
        for resource_type, resource in self.resources.items():
            if resource.amount > 0:
                lines.append(f"  {resource_type.value}: {resource.amount:.1f}")
        return "\n".join(lines)

