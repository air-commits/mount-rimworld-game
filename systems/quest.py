"""
任务系统
管理游戏中的任务和委托
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Callable
from datetime import datetime

from entities.player import Player
from entities.npc import NPC
from utils.logger import get_logger


class QuestStatus(Enum):
    """任务状态"""
    AVAILABLE = "available"      # 可接受
    ACTIVE = "active"            # 进行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败


class QuestType(Enum):
    """任务类型"""
    KILL = "kill"                # 击败敌人
    COLLECT = "collect"          # 收集物品
    DELIVER = "deliver"          # 交付物品
    ESCORT = "escort"            # 护送
    EXPLORE = "explore"          # 探索
    BUILD = "build"              # 建造


@dataclass
class Quest:
    """任务类"""
    quest_id: str                    # 任务ID
    title: str                       # 任务标题
    description: str                 # 任务描述
    quest_type: QuestType            # 任务类型
    giver: Optional[NPC] = None      # 发布任务的NPC
    status: QuestStatus = QuestStatus.AVAILABLE
    
    # 任务目标
    targets: Dict = field(default_factory=dict)  # 目标数据（根据任务类型不同）
    
    # 奖励
    reward_gold: int = 0             # 金币奖励
    reward_exp: int = 0              # 经验奖励
    reward_items: List[str] = field(default_factory=list)  # 物品奖励
    
    # 时间限制（可选）
    time_limit: Optional[float] = None  # 时间限制（秒）
    start_time: Optional[float] = None  # 开始时间
    
    # 完成条件检查函数
    check_completion: Optional[Callable] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.start_time is None and self.status == QuestStatus.ACTIVE:
            import time
            self.start_time = time.time()
    
    def activate(self):
        """激活任务"""
        if self.status == QuestStatus.AVAILABLE:
            self.status = QuestStatus.ACTIVE
            import time
            self.start_time = time.time()
    
    def is_expired(self) -> bool:
        """
        检查任务是否过期
        
        Returns:
            是否过期
        """
        if self.time_limit is None or self.start_time is None:
            return False
        
        import time
        elapsed = time.time() - self.start_time
        return elapsed > self.time_limit
    
    def can_complete(self, player: Player) -> bool:
        """
        检查任务是否可以完成
        
        Args:
            player: 玩家对象
            
        Returns:
            是否可以完成
        """
        if self.status != QuestStatus.ACTIVE:
            return False
        
        if self.is_expired():
            self.status = QuestStatus.FAILED
            return False
        
        # 使用自定义检查函数
        if self.check_completion:
            return self.check_completion(self, player)
        
        # 默认检查逻辑
        if self.quest_type == QuestType.KILL:
            # 检查是否击败了足够的敌人
            kills_needed = self.targets.get("count", 1)
            kills_done = self.targets.get("done", 0)
            return kills_done >= kills_needed
        
        elif self.quest_type == QuestType.COLLECT:
            # 检查是否收集了足够的物品
            item_type = self.targets.get("item_type")
            count_needed = self.targets.get("count", 1)
            count_collected = self.targets.get("collected", 0)
            return count_collected >= count_needed
        
        return False
    
    def complete(self, player: Player):
        """
        完成任务并给予奖励
        
        Args:
            player: 玩家对象
        """
        if not self.can_complete(player):
            return False
        
        self.status = QuestStatus.COMPLETED
        
        # 给予奖励
        if self.reward_gold > 0:
            player.add_money(self.reward_gold)
        
        if self.reward_exp > 0:
            player.add_experience(self.reward_exp)
        
        # 物品奖励（后续实现）
        # for item in self.reward_items:
        #     player.add_item(item)
        
        logger = get_logger("Quest")
        logger.info(f"任务完成: {self.title}")
        
        return True


class QuestManager:
    """任务管理器"""
    
    def __init__(self):
        """初始化任务管理器"""
        self.quests: List[Quest] = []
        self.logger = get_logger("QuestManager")
    
    def add_quest(self, quest: Quest):
        """
        添加任务
        
        Args:
            quest: 任务对象
        """
        self.quests.append(quest)
        self.logger.debug(f"添加任务: {quest.title}")
    
    def get_available_quests(self) -> List[Quest]:
        """
        获取可接受的任务
        
        Returns:
            可接受的任务列表
        """
        return [q for q in self.quests if q.status == QuestStatus.AVAILABLE]
    
    def get_active_quests(self) -> List[Quest]:
        """
        获取进行中的任务
        
        Returns:
            进行中的任务列表
        """
        return [q for q in self.quests if q.status == QuestStatus.ACTIVE]
    
    def get_quest_by_id(self, quest_id: str) -> Optional[Quest]:
        """
        根据ID获取任务
        
        Args:
            quest_id: 任务ID
            
        Returns:
            任务对象（如果存在）
        """
        for quest in self.quests:
            if quest.quest_id == quest_id:
                return quest
        return None
    
    def accept_quest(self, quest_id: str) -> bool:
        """
        接受任务
        
        Args:
            quest_id: 任务ID
            
        Returns:
            是否成功接受
        """
        quest = self.get_quest_by_id(quest_id)
        if quest and quest.status == QuestStatus.AVAILABLE:
            quest.activate()
            return True
        return False
    
    def update_quests(self, player: Player, delta_time: float):
        """
        更新任务状态
        
        Args:
            player: 玩家对象
            delta_time: 时间增量
        """
        for quest in self.get_active_quests():
            # 检查任务是否过期
            if quest.is_expired():
                quest.status = QuestStatus.FAILED
                self.logger.info(f"任务失败（超时）: {quest.title}")
    
    def create_kill_quest(
        self,
        quest_id: str,
        title: str,
        description: str,
        giver: NPC,
        kill_count: int,
        reward_gold: int = 100,
        reward_exp: int = 50
    ) -> Quest:
        """
        创建击败任务
        
        Args:
            quest_id: 任务ID
            title: 任务标题
            description: 任务描述
            giver: 发布任务的NPC
            kill_count: 需要击败的数量
            reward_gold: 金币奖励
            reward_exp: 经验奖励
            
        Returns:
            任务对象
        """
        quest = Quest(
            quest_id=quest_id,
            title=title,
            description=description,
            quest_type=QuestType.KILL,
            giver=giver,
            targets={"count": kill_count, "done": 0},
            reward_gold=reward_gold,
            reward_exp=reward_exp
        )
        return quest
    
    def create_collect_quest(
        self,
        quest_id: str,
        title: str,
        description: str,
        giver: NPC,
        item_type: str,
        count: int,
        reward_gold: int = 80,
        reward_exp: int = 40
    ) -> Quest:
        """
        创建收集任务
        
        Args:
            quest_id: 任务ID
            title: 任务标题
            description: 任务描述
            giver: 发布任务的NPC
            item_type: 物品类型
            count: 需要收集的数量
            reward_gold: 金币奖励
            reward_exp: 经验奖励
            
        Returns:
            任务对象
        """
        quest = Quest(
            quest_id=quest_id,
            title=title,
            description=description,
            quest_type=QuestType.COLLECT,
            giver=giver,
            targets={"item_type": item_type, "count": count, "collected": 0},
            reward_gold=reward_gold,
            reward_exp=reward_exp
        )
        return quest

