"""
角色基类
定义所有角色的基础属性和行为
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum

from core.world import Position


class StatType(Enum):
    """属性类型"""
    STRENGTH = "strength"        # 力量
    DEXTERITY = "dexterity"      # 敏捷
    CONSTITUTION = "constitution"  # 体质
    INTELLIGENCE = "intelligence"  # 智力
    WISDOM = "wisdom"            # 感知
    CHARISMA = "charisma"        # 魅力


@dataclass
class CharacterStats:
    """角色属性"""
    strength: int = 10          # 力量（影响近战伤害）
    dexterity: int = 10         # 敏捷（影响攻击速度和闪避）
    constitution: int = 10      # 体质（影响生命值）
    intelligence: int = 10      # 智力（影响技能学习）
    wisdom: int = 10            # 感知（影响远程命中）
    charisma: int = 10          # 魅力（影响NPC交互）
    
    def get_stat(self, stat_type: StatType) -> int:
        """
        获取指定属性值
        
        Args:
            stat_type: 属性类型
            
        Returns:
            属性值
        """
        return getattr(self, stat_type.value)
    
    def set_stat(self, stat_type: StatType, value: int):
        """
        设置属性值
        
        Args:
            stat_type: 属性类型
            value: 属性值
        """
        setattr(self, stat_type, value)
    
    def modify_stat(self, stat_type: StatType, modifier: int):
        """
        修改属性值
        
        Args:
            stat_type: 属性类型
            modifier: 修改量（可为负）
        """
        current = self.get_stat(stat_type)
        self.set_stat(stat_type, max(0, current + modifier))


class Character:
    """角色基类"""
    
    def __init__(
        self,
        name: str,
        position: Position,
        stats: Optional[CharacterStats] = None
    ):
        """
        初始化角色
        
        Args:
            name: 角色名称
            position: 初始位置
            stats: 角色属性（如为None则使用默认值）
        """
        self.name = name
        self.position = position
        self.stats = stats or CharacterStats()
        
        # 生命值系统
        self.max_health = 100 + (self.stats.constitution * 5)
        self.current_health = self.max_health
        
        # 状态系统
        self.is_alive = True
        self.is_mounted = False  # 是否骑乘
        
        # 装备（后续扩展）
        self.equipped_weapon = None
        self.equipped_armor = None
        
        # 技能和经验（后续扩展）
        self.experience = 0
        self.level = 1
        
        # AI目标（用于移动和战斗）
        self.target_position: Optional[Position] = None
        self.target_entity = None
        
        # 移动速度（基础速度 + 敏捷加成）
        self.base_speed = 50.0
        self.current_speed = self.base_speed + (self.stats.dexterity * 2)
    
    def update(self, delta_time: float):
        """
        更新角色逻辑（子类可重写）
        
        Args:
            delta_time: 时间增量（秒）
        """
        if not self.is_alive:
            return
        
        # 更新移动
        self._update_movement(delta_time)
    
    def _update_movement(self, delta_time: float):
        """
        更新移动逻辑
        
        Args:
            delta_time: 时间增量
        """
        if self.target_position is None:
            return
        
        # 计算移动方向
        direction = Position(
            self.target_position.x - self.position.x,
            self.target_position.y - self.position.y
        )
        distance = (direction.x ** 2 + direction.y ** 2) ** 0.5
        
        # 如果已到达目标位置，清除目标
        if distance < 5.0:
            self.target_position = None
            return
        
        # 归一化方向向量
        if distance > 0:
            direction.x /= distance
            direction.y /= distance
        
        # 移动
        move_distance = self.current_speed * delta_time
        self.position.x += direction.x * move_distance
        self.position.y += direction.y * move_distance
    
    def move_to(self, target: Position):
        """
        移动到目标位置
        
        Args:
            target: 目标位置
        """
        self.target_position = target
    
    def take_damage(self, damage: int) -> int:
        """
        受到伤害
        
        Args:
            damage: 伤害值
            
        Returns:
            实际受到的伤害
        """
        if not self.is_alive:
            return 0
        
        # 计算实际伤害（可以加入护甲减免等）
        actual_damage = max(1, damage)
        self.current_health -= actual_damage
        
        # 检查是否死亡
        if self.current_health <= 0:
            self.current_health = 0
            self.is_alive = False
        
        return actual_damage
    
    def heal(self, amount: int):
        """
        恢复生命值
        
        Args:
            amount: 恢复量
        """
        if not self.is_alive:
            return
        
        self.current_health = min(self.max_health, self.current_health + amount)
    
    def get_health_percentage(self) -> float:
        """
        获取生命值百分比
        
        Returns:
            生命值百分比（0.0-1.0）
        """
        return self.current_health / self.max_health if self.max_health > 0 else 0.0
    
    def calculate_melee_damage(self) -> int:
        """
        计算近战伤害
        
        Returns:
            伤害值
        """
        base_damage = 10
        strength_bonus = self.stats.strength // 2
        return base_damage + strength_bonus
    
    def calculate_ranged_damage(self) -> int:
        """
        计算远程伤害
        
        Returns:
            伤害值
        """
        base_damage = 8
        dexterity_bonus = self.stats.dexterity // 3
        return base_damage + dexterity_bonus
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.name} (Lv.{self.level}) - HP: {self.current_health}/{self.max_health}"

