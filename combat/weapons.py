"""
武器系统
定义各种武器类型和属性
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class WeaponType(Enum):
    """武器类型"""
    SWORD = "sword"              # 剑
    AXE = "axe"                  # 斧
    MACE = "mace"                # 锤
    SPEAR = "spear"              # 长矛
    BOW = "bow"                  # 弓
    CROSSBOW = "crossbow"        # 弩
    DAGGER = "dagger"            # 匕首
    GREATSWORD = "greatsword"    # 巨剑


class DamageType(Enum):
    """伤害类型"""
    SLASH = "slash"      # 劈砍
    PIERCE = "pierce"    # 穿刺
    BLUNT = "blunt"      # 钝击


@dataclass
class Weapon:
    """武器类"""
    name: str                        # 武器名称
    weapon_type: WeaponType          # 武器类型
    damage: int                      # 基础伤害
    damage_type: DamageType          # 伤害类型
    attack_speed: float = 1.0        # 攻击速度（每秒攻击次数）
    range: float = 50.0              # 攻击范围
    can_mounted: bool = False        # 是否可用于骑乘战斗
    durability: int = 100            # 耐久度
    max_durability: int = 100        # 最大耐久度
    
    def get_effective_damage(self) -> int:
        """
        计算有效伤害（考虑耐久度）
        
        Returns:
            有效伤害值
        """
        durability_ratio = self.durability / self.max_durability
        return int(self.damage * (0.5 + 0.5 * durability_ratio))
    
    def use(self, durability_loss: int = 1):
        """
        使用武器（降低耐久度）
        
        Args:
            durability_loss: 耐久度损失
        """
        self.durability = max(0, self.durability - durability_loss)
    
    def repair(self, amount: int):
        """
        修理武器
        
        Args:
            amount: 修理量
        """
        self.durability = min(self.max_durability, self.durability + amount)
    
    def is_broken(self) -> bool:
        """
        检查武器是否损坏
        
        Returns:
            是否损坏
        """
        return self.durability <= 0


# 预定义武器
WEAPONS = {
    "iron_sword": Weapon(
        name="铁剑",
        weapon_type=WeaponType.SWORD,
        damage=15,
        damage_type=DamageType.SLASH,
        attack_speed=1.2,
        range=60.0
    ),
    "longbow": Weapon(
        name="长弓",
        weapon_type=WeaponType.BOW,
        damage=20,
        damage_type=DamageType.PIERCE,
        attack_speed=0.8,
        range=200.0
    ),
    "spear": Weapon(
        name="长矛",
        weapon_type=WeaponType.SPEAR,
        damage=18,
        damage_type=DamageType.PIERCE,
        attack_speed=1.0,
        range=120.0,
        can_mounted=True
    ),
    "axe": Weapon(
        name="战斧",
        weapon_type=WeaponType.AXE,
        damage=22,
        damage_type=DamageType.SLASH,
        attack_speed=0.9,
        range=55.0
    ),
    "dagger": Weapon(
        name="匕首",
        weapon_type=WeaponType.DAGGER,
        damage=12,
        damage_type=DamageType.PIERCE,
        attack_speed=1.5,
        range=40.0
    ),
}

def get_weapon(weapon_name: str) -> Optional[Weapon]:
    """
    根据名称获取武器（返回副本）
    
    Args:
        weapon_name: 武器名称
        
    Returns:
        武器对象（如果存在）
    """
    if weapon_name in WEAPONS:
        # 返回武器的副本，避免共享状态
        import copy
        return copy.deepcopy(WEAPONS[weapon_name])
    return None

