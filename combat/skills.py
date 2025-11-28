"""
技能系统
定义角色技能和技能效果
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Callable, Optional


class SkillType(Enum):
    """技能类型"""
    # 战斗技能
    ONE_HANDED = "one_handed"        # 单手武器
    TWO_HANDED = "two_handed"        # 双手武器
    ARCHERY = "archery"              # 弓箭
    POLEARM = "polearm"              # 长柄武器
    RIDING = "riding"                # 骑术
    SHIELD = "shield"                # 盾牌
    
    # 非战斗技能
    TRADING = "trading"              # 交易
    LEADERSHIP = "leadership"        # 领导力
    ENGINEERING = "engineering"      # 工程学
    MEDICINE = "medicine"            # 医学
    CRAFTING = "crafting"            # 制造


@dataclass
class Skill:
    """技能类"""
    skill_type: SkillType    # 技能类型
    level: int = 0           # 技能等级（0-100）
    experience: int = 0      # 技能经验值
    
    def add_experience(self, amount: int):
        """
        增加技能经验
        
        Args:
            amount: 经验值
        """
        self.experience += amount
        
        # 每100经验升1级（等级越高需要越多经验）
        required_exp = (self.level + 1) * 100
        while self.experience >= required_exp and self.level < 100:
            self.level += 1
            self.experience -= required_exp
            required_exp = (self.level + 1) * 100
    
    def get_effectiveness(self) -> float:
        """
        获取技能效果（0.0-1.0）
        
        Returns:
            技能效果值
        """
        return self.level / 100.0


class SkillManager:
    """技能管理器"""
    
    def __init__(self):
        """初始化技能管理器"""
        self.skills: Dict[SkillType, Skill] = {}
        
        # 初始化所有技能
        for skill_type in SkillType:
            self.skills[skill_type] = Skill(skill_type=skill_type)
    
    def get_skill(self, skill_type: SkillType) -> Skill:
        """
        获取指定技能
        
        Args:
            skill_type: 技能类型
            
        Returns:
            技能对象
        """
        return self.skills.get(skill_type, Skill(skill_type=skill_type))
    
    def add_experience(self, skill_type: SkillType, amount: int):
        """
        为指定技能增加经验
        
        Args:
            skill_type: 技能类型
            amount: 经验值
        """
        if skill_type not in self.skills:
            self.skills[skill_type] = Skill(skill_type=skill_type)
        self.skills[skill_type].add_experience(amount)
    
    def get_total_skill_points(self) -> int:
        """
        获取总技能点数
        
        Returns:
            总技能点数
        """
        return sum(skill.level for skill in self.skills.values())

