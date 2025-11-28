"""
战斗引擎
处理战斗逻辑和伤害计算
"""

import random
from dataclasses import dataclass
from typing import Optional

from entities.character import Character
from combat.weapons import Weapon
from combat.skills import SkillType, SkillManager


@dataclass
class CombatResult:
    """战斗结果"""
    attacker: Character          # 攻击者
    defender: Character          # 防御者
    damage_dealt: int            # 造成的伤害
    is_critical: bool = False    # 是否暴击
    is_miss: bool = False        # 是否未命中
    is_blocked: bool = False     # 是否被格挡
    attack_succeeded: bool = True  # 是否成功发起攻击（用于冷却时间检查）
    
    def __str__(self) -> str:
        """字符串表示"""
        if not self.attack_succeeded:
            return f"{self.attacker.name} 攻击冷却中..."
        elif self.is_miss:
            return f"{self.attacker.name} 未命中 {self.defender.name}"
        elif self.is_blocked:
            return f"{self.attacker.name} 的攻击被 {self.defender.name} 格挡"
        elif self.is_critical:
            return f"{self.attacker.name} 对 {self.defender.name} 造成 {self.damage_dealt} 点暴击伤害！"
        else:
            return f"{self.attacker.name} 对 {self.defender.name} 造成 {self.damage_dealt} 点伤害"


class CombatEngine:
    """战斗引擎"""
    
    def __init__(self):
        """初始化战斗引擎"""
        self.base_critical_chance = 0.1  # 基础暴击率
        self.base_miss_chance = 0.05     # 基础未命中率
    
    def calculate_attack(
        self,
        attacker: Character,
        defender: Character,
        weapon: Optional[Weapon] = None,
        skill_manager: Optional[SkillManager] = None
    ) -> CombatResult:
        """
        计算一次攻击
        
        Args:
            attacker: 攻击者
            defender: 防御者
            weapon: 使用的武器（如为None则使用徒手）
            skill_manager: 技能管理器（用于计算技能加成）
            
        Returns:
            战斗结果
        """
        result = CombatResult(
            attacker=attacker,
            defender=defender,
            damage_dealt=0,
            attack_succeeded=True  # calculate_attack直接调用时，假设已经过了冷却检查
        )
        
        # 检查是否命中
        miss_chance = self._calculate_miss_chance(attacker, defender, skill_manager)
        if random.random() < miss_chance:
            result.is_miss = True
            return result
        
        # 检查是否被格挡（简化处理）
        block_chance = self._calculate_block_chance(defender, skill_manager)
        if random.random() < block_chance:
            result.is_blocked = True
            return result
        
        # 计算伤害
        base_damage = 0
        if weapon:
            base_damage = weapon.get_effective_damage()
            # 使用武器，降低耐久度
            weapon.use()
        else:
            # 徒手伤害
            base_damage = attacker.calculate_melee_damage()
        
        # 应用属性加成
        if weapon and weapon.weapon_type.value in ['bow', 'crossbow']:
            # 远程武器使用敏捷
            stat_bonus = attacker.stats.dexterity // 2
        else:
            # 近战武器使用力量
            stat_bonus = attacker.stats.strength // 2
        
        # 技能加成
        skill_bonus = 0
        if skill_manager and weapon:
            skill = self._get_relevant_skill(weapon.weapon_type, skill_manager)
            skill_bonus = int(base_damage * skill.get_effectiveness() * 0.3)
        
        damage = base_damage + stat_bonus + skill_bonus
        
        # 检查暴击
        critical_chance = self._calculate_critical_chance(attacker, skill_manager)
        if random.random() < critical_chance:
            damage = int(damage * 1.5)
            result.is_critical = True
        
        result.damage_dealt = damage
        
        # 应用伤害
        defender.take_damage(damage)
        
        return result
    
    def _calculate_miss_chance(
        self,
        attacker: Character,
        defender: Character,
        skill_manager: Optional[SkillManager]
    ) -> float:
        """
        计算未命中率
        
        Args:
            attacker: 攻击者
            defender: 防御者
            skill_manager: 技能管理器
            
        Returns:
            未命中率（0.0-1.0）
        """
        miss_chance = self.base_miss_chance
        
        # 攻击者敏捷降低未命中率
        miss_chance -= attacker.stats.dexterity / 200.0
        
        # 防御者敏捷增加攻击者未命中率
        miss_chance += defender.stats.dexterity / 300.0
        
        return max(0.0, min(0.5, miss_chance))
    
    def _calculate_block_chance(
        self,
        defender: Character,
        skill_manager: Optional[SkillManager]
    ) -> float:
        """
        计算格挡率
        
        Args:
            defender: 防御者
            skill_manager: 技能管理器
            
        Returns:
            格挡率（0.0-1.0）
        """
        # 简化处理，如果有盾牌技能则增加格挡率
        block_chance = 0.05
        
        if skill_manager:
            shield_skill = skill_manager.get_skill(SkillType.SHIELD)
            block_chance += shield_skill.get_effectiveness() * 0.2
        
        return min(0.5, block_chance)
    
    def _calculate_critical_chance(
        self,
        attacker: Character,
        skill_manager: Optional[SkillManager]
    ) -> float:
        """
        计算暴击率
        
        Args:
            attacker: 攻击者
            skill_manager: 技能管理器
            
        Returns:
            暴击率（0.0-1.0）
        """
        critical_chance = self.base_critical_chance
        
        # 敏捷增加暴击率
        critical_chance += attacker.stats.dexterity / 200.0
        
        return min(0.5, critical_chance)
    
    def _get_relevant_skill(self, weapon_type, skill_manager: SkillManager):
        """
        获取与武器相关的技能
        
        Args:
            weapon_type: 武器类型
            skill_manager: 技能管理器
            
        Returns:
            相关技能对象
        """
        from combat.weapons import WeaponType
        
        # 根据武器类型映射到技能类型
        skill_mapping = {
            WeaponType.SWORD: SkillType.ONE_HANDED,
            WeaponType.AXE: SkillType.ONE_HANDED,
            WeaponType.MACE: SkillType.ONE_HANDED,
            WeaponType.DAGGER: SkillType.ONE_HANDED,
            WeaponType.GREATSWORD: SkillType.TWO_HANDED,
            WeaponType.SPEAR: SkillType.POLEARM,
            WeaponType.BOW: SkillType.ARCHERY,
            WeaponType.CROSSBOW: SkillType.ARCHERY,
        }
        
        skill_type = skill_mapping.get(weapon_type, SkillType.ONE_HANDED)
        return skill_manager.get_skill(skill_type)
    
    def can_attack(
        self,
        attacker: Character,
        defender: Character,
        weapon: Optional[Weapon] = None
    ) -> bool:
        """
        检查是否可以攻击（距离检查）
        
        Args:
            attacker: 攻击者
            defender: 防御者
            weapon: 武器
            
        Returns:
            是否可以攻击
        """
        distance = attacker.position.distance_to(defender.position)
        
        if weapon:
            return distance <= weapon.range
        else:
            # 徒手攻击范围
            return distance <= 50.0
    
    def process_combat_round(
        self,
        attacker: Character,
        defender: Character,
        time_current: float,
        weapon: Optional[Weapon] = None,
        skill_manager: Optional[SkillManager] = None
    ) -> CombatResult:
        """
        处理战斗回合（包含攻击冷却时间检查）
        
        Args:
            attacker: 攻击者
            defender: 防御者
            time_current: 当前游戏时间
            weapon: 使用的武器（如为None则使用徒手）
            skill_manager: 技能管理器（用于计算技能加成）
            
        Returns:
            战斗结果（如果冷却时间未到，attack_succeeded为False）
        """
        # 初始化攻击者属性（如果不存在）
        if not hasattr(attacker, 'last_attack_time'):
            attacker.last_attack_time = 0.0
        
        # 计算攻击速度（攻击间隔，秒/次）
        attack_speed = 1.0  # 默认1.0秒/次
        
        # 如果角色有attack_speed属性，使用它
        if hasattr(attacker, 'attack_speed'):
            attack_speed = attacker.attack_speed
        elif weapon:
            # 如果角色没有attack_speed，但装备了武器，使用武器的攻击速度
            # attack_speed是每秒攻击次数，需要转换为攻击间隔
            if weapon.attack_speed > 0:
                attack_speed = 1.0 / weapon.attack_speed
        else:
            # 徒手攻击，根据敏捷计算攻击速度
            # 敏捷越高，攻击越快（最小0.5秒/次）
            base_attack_speed = 1.0
            dexterity_bonus = attacker.stats.dexterity / 100.0
            attack_speed = max(0.5, base_attack_speed - dexterity_bonus * 0.3)
        
        # 检查攻击冷却时间
        time_since_last_attack = time_current - attacker.last_attack_time
        
        if time_since_last_attack < attack_speed:
            # 冷却时间未到，返回失败结果
            result = CombatResult(
                attacker=attacker,
                defender=defender,
                damage_dealt=0,
                attack_succeeded=False
            )
            return result
        
        # 冷却时间已到，执行攻击
        result = self.calculate_attack(
            attacker=attacker,
            defender=defender,
            weapon=weapon,
            skill_manager=skill_manager
        )
        
        # 更新攻击时间
        attacker.last_attack_time = time_current
        result.attack_succeeded = True
        
        return result
    
    def get_attack_cooldown_remaining(
        self,
        attacker: Character,
        time_current: float,
        weapon: Optional[Weapon] = None
    ) -> float:
        """
        获取剩余攻击冷却时间
        
        Args:
            attacker: 攻击者
            time_current: 当前游戏时间
            weapon: 使用的武器（如为None则使用徒手）
            
        Returns:
            剩余冷却时间（秒），如果为0或负数表示可以攻击
        """
        if not hasattr(attacker, 'last_attack_time'):
            return 0.0
        
        # 计算攻击速度（与process_combat_round逻辑一致）
        attack_speed = 1.0
        if hasattr(attacker, 'attack_speed'):
            attack_speed = attacker.attack_speed
        elif weapon and weapon.attack_speed > 0:
            attack_speed = 1.0 / weapon.attack_speed
        
        time_since_last_attack = time_current - attacker.last_attack_time
        remaining = attack_speed - time_since_last_attack
        
        return max(0.0, remaining)

