"""
NPC角色类
继承自Character，添加NPC特有的行为和AI功能
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum

from entities.character import Character, CharacterStats
from core.world import Position


class NPCMood(Enum):
    """NPC情绪状态"""
    HAPPY = "happy"          # 开心
    NEUTRAL = "neutral"      # 中性
    SAD = "sad"              # 悲伤
    ANGRY = "angry"          # 愤怒
    STRESSED = "stressed"    # 压力大


class NPCRelationship(Enum):
    """与玩家的关系"""
    ALLY = "ally"            # 盟友
    FRIEND = "friend"        # 朋友
    NEUTRAL = "neutral"      # 中立
    ENEMY = "enemy"          # 敌人
    HOSTILE = "hostile"      # 敌对


@dataclass
class NPCPersonality:
    """NPC个性特征"""
    # 个性标签
    traits: List[str]  # 特征列表，如 ['brave', 'kind', 'lazy']
    
    # 性格倾向（0-100）
    kindness: int = 50       # 友善度
    aggression: int = 50     # 攻击性
    loyalty: int = 50        # 忠诚度
    curiosity: int = 50      # 好奇心
    
    # 职业/角色
    profession: str = "commoner"  # 职业
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.traits:
            self.traits = []


class NPC(Character):
    """NPC角色"""
    
    def __init__(
        self,
        name: str,
        position: Position,
        personality: Optional[NPCPersonality] = None,
        stats: Optional[CharacterStats] = None
    ):
        """
        初始化NPC
        
        Args:
            name: NPC名称
            position: 初始位置
            personality: NPC个性（如为None则随机生成）
            stats: 角色属性
        """
        super().__init__(name, position, stats)
        
        # NPC个性
        self.personality = personality or NPCPersonality(traits=[])
        
        # 势力系统（用于大地图交互）
        self.faction = "neutral"  # 势力：neutral, enemy, bandit, alliance 等
        
        # 实体类型标记（用于区分大地图军团和局部地图NPC）
        self.is_world_entity = True  # True=大地图军团，False=局部地图NPC（村民等）
        
        # 关系系统
        self.relationship_with_player = NPCRelationship.NEUTRAL
        self.relationship_value = 0  # 关系值（-100到100）
        
        # 情绪系统
        self.mood = NPCMood.NEUTRAL
        self.mood_value = 50  # 情绪值（0-100）
        
        # 需求系统（环世界风格）
        self.needs = {
            "food": 100.0,      # 食物需求（0-100）
            "rest": 100.0,      # 休息需求
            "entertainment": 50.0,  # 娱乐需求
            "safety": 70.0      # 安全感
        }
        
        # AI行为
        self.current_activity = None  # 当前活动
        self.ai_state = "idle"  # AI状态：idle, moving, working, fighting
        
        # 对话历史（用于OpenAI集成）
        self.conversation_history: List[Dict[str, str]] = []
        
        # 任务相关
        self.available_quests = []  # 可提供的任务
        self.active_quests = []     # 正在进行的任务
    
    def update(self, delta_time: float):
        """
        更新NPC逻辑
        
        Args:
            delta_time: 时间增量
        """
        super().update(delta_time)
        
        if not self.is_alive:
            return
        
        # 更新需求（需求会随时间降低）
        self._update_needs(delta_time)
        
        # 根据需求更新情绪
        self._update_mood()
        
        # 执行AI行为
        self._update_ai(delta_time)
    
    def _update_needs(self, delta_time: float):
        """
        更新需求值（需求随时间降低）
        
        Args:
            delta_time: 时间增量
        """
        # 每秒降低一定需求值
        decay_rate = 1.0  # 每秒降低1点
        
        self.needs["food"] = max(0, self.needs["food"] - decay_rate * delta_time)
        self.needs["rest"] = max(0, self.needs["rest"] - decay_rate * delta_time * 0.5)
        self.needs["entertainment"] = max(0, self.needs["entertainment"] - decay_rate * delta_time * 0.3)
        self.needs["safety"] = max(0, self.needs["safety"] - decay_rate * delta_time * 0.2)
    
    def _update_mood(self):
        """根据需求更新情绪"""
        # 计算平均需求
        avg_need = sum(self.needs.values()) / len(self.needs)
        
        # 根据平均需求设置情绪
        if avg_need >= 80:
            self.mood = NPCMood.HAPPY
            self.mood_value = 80 + (avg_need - 80)
        elif avg_need >= 50:
            self.mood = NPCMood.NEUTRAL
            self.mood_value = 50 + (avg_need - 50) * 0.6
        elif avg_need >= 30:
            self.mood = NPCMood.SAD
            self.mood_value = 30 + (avg_need - 30) * 0.6
        else:
            self.mood = NPCMood.STRESSED
            self.mood_value = avg_need
        
        self.mood_value = min(100, max(0, self.mood_value))
    
    def _update_ai(self, delta_time: float):
        """
        更新AI行为（基础AI，后续可接入OpenAI）
        
        Args:
            delta_time: 时间增量
        """
        # 简单AI逻辑
        if self.ai_state == "idle":
            # 检查需求，决定下一步行动
            if self.needs["food"] < 50:
                self.ai_state = "seeking_food"
            elif self.needs["rest"] < 30:
                self.ai_state = "resting"
        elif self.ai_state == "seeking_food":
            # 寻找食物（这里简化处理）
            pass
        elif self.ai_state == "resting":
            # 休息恢复需求
            self.needs["rest"] = min(100, self.needs["rest"] + 10 * delta_time)
            if self.needs["rest"] >= 80:
                self.ai_state = "idle"
    
    def fulfill_need(self, need_type: str, amount: float):
        """
        满足NPC的需求
        
        Args:
            need_type: 需求类型
            amount: 满足量
        """
        if need_type in self.needs:
            self.needs[need_type] = min(100.0, self.needs[need_type] + amount)
    
    def modify_relationship(self, value: int):
        """
        修改与玩家的关系值
        
        Args:
            value: 关系变化值（可为负）
        """
        self.relationship_value = max(-100, min(100, self.relationship_value + value))
        
        # 根据关系值更新关系类型
        if self.relationship_value >= 80:
            self.relationship_with_player = NPCRelationship.ALLY
        elif self.relationship_value >= 50:
            self.relationship_with_player = NPCRelationship.FRIEND
        elif self.relationship_value >= -50:
            self.relationship_with_player = NPCRelationship.NEUTRAL
        elif self.relationship_value >= -80:
            self.relationship_with_player = NPCRelationship.ENEMY
        else:
            self.relationship_with_player = NPCRelationship.HOSTILE
    
    def add_conversation(self, speaker: str, message: str):
        """
        添加对话到历史记录（用于OpenAI上下文）
        
        Args:
            speaker: 说话者（"player" 或 NPC名称）
            message: 对话内容
        """
        self.conversation_history.append({
            "speaker": speaker,
            "message": message
        })
        
        # 限制历史记录长度（保留最近20条）
        if len(self.conversation_history) > 20:
            self.conversation_history.pop(0)
    
    def get_conversation_context(self) -> str:
        """
        获取对话上下文（用于OpenAI）
        
        Returns:
            对话上下文字符串
        """
        context = f"NPC: {self.name}\n个性: {', '.join(self.personality.traits)}\n"
        context += f"情绪: {self.mood.value}\n关系: {self.relationship_with_player.value}\n\n对话历史:\n"
        
        for conv in self.conversation_history[-10:]:  # 最近10条
            context += f"{conv['speaker']}: {conv['message']}\n"
        
        return context

