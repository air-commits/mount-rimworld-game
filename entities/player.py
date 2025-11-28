"""
玩家角色类
继承自Character，添加玩家特有的功能
"""

from typing import Optional, List

from entities.character import Character, CharacterStats
from core.world import Position


class Player(Character):
    """玩家角色"""
    
    def __init__(
        self,
        name: str = "玩家",
        position: Optional[Position] = None,
        stats: Optional[CharacterStats] = None
    ):
        """
        初始化玩家角色
        
        Args:
            name: 玩家名称
            position: 初始位置（如为None则在(0,0)）
            stats: 角色属性
        """
        if position is None:
            position = Position(0, 0)
        
        super().__init__(name, position, stats)
        
        # 玩家特有的属性
        self.money = 1000  # 金币
        self.reputation = 0  # 声望
        self.owned_colonies = []  # 拥有的基地列表
        
        # 玩家控制状态
        self.can_control = True
        
        # 军团模式：玩家的队伍
        self.party: List[Character] = []
        # 将玩家自己加入到队伍的第一个位置
        self.party.append(self)
    
    def add_money(self, amount: int):
        """
        增加金币
        
        Args:
            amount: 金币数量（可为负）
        """
        self.money = max(0, self.money + amount)
    
    def can_afford(self, cost: int) -> bool:
        """
        检查是否有足够的金币
        
        Args:
            cost: 花费
            
        Returns:
            是否负担得起
        """
        return self.money >= cost
    
    def add_experience(self, amount: int):
        """
        增加经验值
        
        Args:
            amount: 经验值
        """
        self.experience += amount
        
        # 检查升级（每100经验升1级）
        while self.experience >= self.level * 100:
            self.level_up()
    
    def level_up(self):
        """角色升级"""
        self.level += 1
        old_max_health = self.max_health
        
        # 升级时增加属性点和生命值
        self.max_health += 10 + (self.stats.constitution // 2)
        self.current_health += (self.max_health - old_max_health)  # 恢复增加的生命值
        
        # 可以在这里添加技能点分配等
        print(f"{self.name} 升级到 {self.level} 级！")
    
    def add_member(self, character: Character):
        """
        添加队员到军团
        
        Args:
            character: 要添加的角色
        """
        if character not in self.party:
            self.party.append(character)
            print(f"{character.name} 加入了你的队伍。")
    
    def remove_member(self, character: Character):
        """
        从军团中移除队员
        
        Args:
            character: 要移除的角色
        """
        if character in self.party and character is not self:
            self.party.remove(character)
            print(f"{character.name} 离开了你的队伍。")
        elif character is self:
            print("不能移除玩家自己。")
    
    def get_total_strength(self) -> int:
        """
        计算队伍所有成员的战斗力总和（用于大地图上的自动战斗预判）
        
        Returns:
            队伍总战斗力
        """
        total_strength = 0
        
        for member in self.party:
            if not hasattr(member, 'is_alive') or member.is_alive:
                # 基础战斗力计算：等级 + 各项属性总和 / 10
                base_strength = member.level
                
                # 属性加成
                if hasattr(member, 'stats'):
                    stat_bonus = (
                        member.stats.strength +
                        member.stats.dexterity +
                        member.stats.constitution +
                        member.stats.intelligence +
                        member.stats.wisdom +
                        member.stats.charisma
                    ) // 10
                    
                    # 生命值加成（当前生命值比例）
                    health_ratio = member.current_health / max(member.max_health, 1)
                    health_bonus = int(base_strength * health_ratio * 0.5)
                    
                    total_strength += base_strength + stat_bonus + health_bonus
        
        return total_strength
    
    def get_party_size(self) -> int:
        """
        获取队伍大小
        
        Returns:
            队伍成员数量
        """
        return len(self.party)
    
    def get_alive_members(self) -> List[Character]:
        """
        获取所有存活的队员
        
        Returns:
            存活的队员列表
        """
        return [member for member in self.party 
                if hasattr(member, 'is_alive') and member.is_alive]

