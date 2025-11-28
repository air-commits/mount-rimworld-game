"""
生产系统
处理资源生产和制作配方
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from colony.resource import ResourceType, ResourceManager
from colony.building import Building


@dataclass
class ProductionRecipe:
    """生产配方"""
    name: str                          # 配方名称
    inputs: Dict[ResourceType, float]  # 输入资源
    outputs: Dict[ResourceType, float] # 输出资源
    time_required: float = 1.0         # 所需时间（秒）
    building_type: Optional[str] = None  # 需要的建筑类型
    
    def can_craft(self, resource_manager: ResourceManager) -> bool:
        """
        检查是否可以制作（资源是否足够）
        
        Args:
            resource_manager: 资源管理器
            
        Returns:
            是否可以制作
        """
        return resource_manager.has_resources(self.inputs)


class ProductionSystem:
    """生产系统"""
    
    def __init__(self, resource_manager: ResourceManager):
        """
        初始化生产系统
        
        Args:
            resource_manager: 资源管理器
        """
        self.resource_manager = resource_manager
        self.recipes: List[ProductionRecipe] = []
        self.active_productions: List[Dict] = []  # 正在进行的生产
        
        # 初始化默认配方
        self._init_default_recipes()
    
    def _init_default_recipes(self):
        """初始化默认生产配方"""
        # 食物配方
        self.recipes.append(ProductionRecipe(
            name="烹饪",
            inputs={ResourceType.FOOD: 2},  # 需要2单位食物
            outputs={ResourceType.FOOD: 3},  # 产出3单位（更好的食物）
            time_required=5.0,
            building_type="kitchen"
        ))
        
        # 工具配方
        self.recipes.append(ProductionRecipe(
            name="制作工具",
            inputs={ResourceType.METAL: 5, ResourceType.WOOD: 2},
            outputs={},  # 工具不存储在资源中，而是作为物品
            time_required=10.0,
            building_type="workshop"
        ))
        
        # 建筑材料配方
        self.recipes.append(ProductionRecipe(
            name="加工木材",
            inputs={ResourceType.WOOD: 1},
            outputs={ResourceType.WOOD: 1},  # 加工后的木材（质量更好）
            time_required=2.0,
            building_type="workshop"
        ))
    
    def add_recipe(self, recipe: ProductionRecipe):
        """
        添加生产配方
        
        Args:
            recipe: 配方对象
        """
        self.recipes.append(recipe)
    
    def get_recipe(self, name: str) -> Optional[ProductionRecipe]:
        """
        根据名称获取配方
        
        Args:
            name: 配方名称
            
        Returns:
            配方对象（如果存在）
        """
        for recipe in self.recipes:
            if recipe.name == name:
                return recipe
        return None
    
    def start_production(self, recipe_name: str) -> bool:
        """
        开始生产
        
        Args:
            recipe_name: 配方名称
            
        Returns:
            是否成功开始
        """
        recipe = self.get_recipe(recipe_name)
        if not recipe:
            return False
        
        if not recipe.can_craft(self.resource_manager):
            return False
        
        # 消耗输入资源
        for resource_type, amount in recipe.inputs.items():
            self.resource_manager.remove_resource(resource_type, amount)
        
        # 添加到生产队列
        self.active_productions.append({
            "recipe": recipe,
            "time_remaining": recipe.time_required,
            "completed": False
        })
        
        return True
    
    def update(self, delta_time: float):
        """
        更新生产系统
        
        Args:
            delta_time: 时间增量（秒）
        """
        # 更新所有正在进行的生产
        for production in self.active_productions[:]:
            if production["completed"]:
                continue
            
            production["time_remaining"] -= delta_time
            
            # 检查是否完成
            if production["time_remaining"] <= 0:
                recipe = production["recipe"]
                
                # 产出资源
                for resource_type, amount in recipe.outputs.items():
                    self.resource_manager.add_resource(resource_type, amount)
                
                production["completed"] = True
        
        # 移除已完成的生产
        self.active_productions = [
            p for p in self.active_productions if not p["completed"]
        ]
    
    def get_production_status(self) -> List[Dict]:
        """
        获取当前生产状态
        
        Returns:
            生产状态列表
        """
        return [
            {
                "recipe": prod["recipe"].name,
                "time_remaining": prod["time_remaining"],
                "progress": 1.0 - (prod["time_remaining"] / prod["recipe"].time_required)
            }
            for prod in self.active_productions if not prod["completed"]
        ]

