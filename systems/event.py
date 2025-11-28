"""
随机事件系统
管理游戏中的随机事件
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Callable
import random
import time

from entities.player import Player
from colony.resource import ResourceManager, ResourceType
from utils.logger import get_logger


class EventType(Enum):
    """事件类型"""
    GOOD_WEATHER = "good_weather"        # 好天气（资源产量增加）
    BAD_WEATHER = "bad_weather"          # 坏天气（资源产量减少）
    MERCHANT_ARRIVAL = "merchant"        # 商人到达
    BANDIT_ATTACK = "bandit_attack"      # 盗贼袭击
    WINDfall = "windfall"                # 意外收获
    DISASTER = "disaster"                # 灾难
    DISCOVERY = "discovery"              # 发现


@dataclass
class GameEvent:
    """游戏事件"""
    event_id: str                        # 事件ID
    event_type: EventType                # 事件类型
    title: str                           # 事件标题
    description: str                     # 事件描述
    duration: float = 0.0                # 持续时间（秒），0表示瞬时事件
    start_time: Optional[float] = None   # 开始时间
    
    # 事件效果
    effects: Dict = None                 # 效果字典
    
    # 事件选项（可选）
    choices: List[Dict] = None           # 选项列表
    
    # 处理函数
    on_start: Optional[Callable] = None  # 事件开始时调用
    on_end: Optional[Callable] = None    # 事件结束时调用
    on_tick: Optional[Callable] = None   # 每帧调用（持续事件）
    
    def __post_init__(self):
        """初始化后处理"""
        if self.effects is None:
            self.effects = {}
        if self.choices is None:
            self.choices = []
        if self.start_time is None and self.duration > 0:
            self.start_time = time.time()
    
    def is_active(self) -> bool:
        """
        检查事件是否正在进行中
        
        Returns:
            是否正在进行
        """
        if self.duration == 0:
            return self.start_time is not None
        
        if self.start_time is None:
            return False
        
        elapsed = time.time() - self.start_time
        return elapsed < self.duration
    
    def start(self):
        """开始事件"""
        self.start_time = time.time()
        if self.on_start:
            self.on_start(self)
    
    def end(self):
        """结束事件"""
        if self.on_end:
            self.on_end(self)
    
    def tick(self, delta_time: float):
        """
        更新事件（持续事件）
        
        Args:
            delta_time: 时间增量
        """
        if self.on_tick:
            self.on_tick(self, delta_time)
        
        # 检查是否应该结束
        if self.duration > 0 and self.start_time is not None:
            elapsed = time.time() - self.start_time
            if elapsed >= self.duration:
                self.end()


class EventManager:
    """事件管理器"""
    
    def __init__(self):
        """初始化事件管理器"""
        self.active_events: List[GameEvent] = []
        self.event_history: List[GameEvent] = []
        self.logger = get_logger("EventManager")
        
        # 事件触发概率和间隔
        self.event_interval = 60.0  # 每60秒检查一次事件
        self.last_event_check = time.time()
        self.event_chance = 0.3  # 30%概率触发事件
    
    def add_event(self, event: GameEvent):
        """
        添加事件
        
        Args:
            event: 事件对象
        """
        event.start()
        self.active_events.append(event)
        self.logger.info(f"事件触发: {event.title}")
        
        # 瞬时事件立即结束
        if event.duration == 0:
            event.end()
            self.active_events.remove(event)
            self.event_history.append(event)
    
    def update(self, delta_time: float, player: Player, resource_manager: ResourceManager):
        """
        更新事件系统
        
        Args:
            delta_time: 时间增量
            player: 玩家对象
            resource_manager: 资源管理器
        """
        current_time = time.time()
        
        # 更新活跃事件
        for event in self.active_events[:]:
            event.tick(delta_time)
            
            if not event.is_active():
                event.end()
                self.active_events.remove(event)
                self.event_history.append(event)
        
        # 定期检查是否触发新事件
        if current_time - self.last_event_check >= self.event_interval:
            self.last_event_check = current_time
            
            if random.random() < self.event_chance:
                self.trigger_random_event(player, resource_manager)
    
    def trigger_random_event(self, player: Player, resource_manager: ResourceManager):
        """
        触发随机事件
        
        Args:
            player: 玩家对象
            resource_manager: 资源管理器
        """
        # 选择事件类型
        event_types = list(EventType)
        event_type = random.choice(event_types)
        
        # 根据类型创建事件
        if event_type == EventType.GOOD_WEATHER:
            event = self.create_good_weather_event()
        elif event_type == EventType.BAD_WEATHER:
            event = self.create_bad_weather_event()
        elif event_type == EventType.MERCHANT_ARRIVAL:
            event = self.create_merchant_event()
        elif event_type == EventType.WINDfall:
            event = self.create_windfall_event(resource_manager)
        elif event_type == EventType.BANDIT_ATTACK:
            event = self.create_bandit_attack_event()
        else:
            event = self.create_generic_event(event_type)
        
        self.add_event(event)
    
    def create_good_weather_event(self) -> GameEvent:
        """创建好天气事件"""
        def on_start(event: GameEvent):
            # 资源产量增加50%
            event.effects["production_bonus"] = 0.5
        
        def on_end(event: GameEvent):
            event.effects.clear()
        
        return GameEvent(
            event_id=f"good_weather_{int(time.time())}",
            event_type=EventType.GOOD_WEATHER,
            title="好天气",
            description="今天天气非常好，资源产量增加了！",
            duration=300.0,  # 持续5分钟
            on_start=on_start,
            on_end=on_end
        )
    
    def create_bad_weather_event(self) -> GameEvent:
        """创建坏天气事件"""
        def on_start(event: GameEvent):
            event.effects["production_penalty"] = 0.3
        
        def on_end(event: GameEvent):
            event.effects.clear()
        
        return GameEvent(
            event_id=f"bad_weather_{int(time.time())}",
            event_type=EventType.BAD_WEATHER,
            title="恶劣天气",
            description="天气变得恶劣，资源产量减少了。",
            duration=180.0,  # 持续3分钟
            on_start=on_start,
            on_end=on_end
        )
    
    def create_merchant_event(self) -> GameEvent:
        """创建商人到达事件"""
        return GameEvent(
            event_id=f"merchant_{int(time.time())}",
            event_type=EventType.MERCHANT_ARRIVAL,
            title="商人到达",
            description="一个商人来到了你的基地，可以和他交易！",
            duration=600.0,  # 持续10分钟
            choices=[
                {"text": "查看商品", "action": "view_merchant"},
                {"text": "忽略", "action": "ignore"}
            ]
        )
    
    def create_windfall_event(self, resource_manager: ResourceManager) -> GameEvent:
        """创建意外收获事件"""
        def on_start(event: GameEvent):
            # 随机获得资源
            resource_type = random.choice(list(ResourceType))
            amount = random.randint(10, 50)
            resource_manager.add_resource(resource_type, amount)
            event.effects["resource_gained"] = (resource_type.value, amount)
        
        return GameEvent(
            event_id=f"windfall_{int(time.time())}",
            event_type=EventType.WINDfall,
            title="意外收获",
            description=f"你发现了一些资源！",
            duration=0.0,  # 瞬时事件
            on_start=on_start
        )
    
    def create_bandit_attack_event(self) -> GameEvent:
        """创建盗贼袭击事件"""
        def on_start(event: GameEvent):
            event.effects["enemies_spawned"] = random.randint(2, 5)
        
        return GameEvent(
            event_id=f"bandit_{int(time.time())}",
            event_type=EventType.BANDIT_ATTACK,
            title="盗贼袭击！",
            description="一群盗贼袭击了你的基地！",
            duration=0.0,
            on_start=on_start,
            choices=[
                {"text": "准备战斗", "action": "fight"},
                {"text": "尝试谈判", "action": "negotiate"}
            ]
        )
    
    def create_generic_event(self, event_type: EventType) -> GameEvent:
        """创建通用事件"""
        return GameEvent(
            event_id=f"{event_type.value}_{int(time.time())}",
            event_type=event_type,
            title=event_type.value.replace("_", " ").title(),
            description="一个事件发生了。",
            duration=0.0
        )
    
    def get_active_events(self) -> List[GameEvent]:
        """
        获取当前活跃的事件
        
        Returns:
            活跃事件列表
        """
        return self.active_events.copy()

