"""
NPC基础AI系统
处理NPC的基本行为决策
"""

from enum import Enum
from typing import Optional, List

from entities.npc import NPC, NPCMood, NPCRelationship
from core.world import Position
from utils.logger import get_logger
from combat.combat_engine import CombatEngine


class AIState(Enum):
    """AI状态"""
    IDLE = "idle"                    # 空闲
    MOVING = "moving"                # 移动中
    WORKING = "working"              # 工作中
    SEEKING_FOOD = "seeking_food"    # 寻找食物
    RESTING = "resting"              # 休息中
    COMBAT = "combat"                # 战斗中
    TALKING = "talking"              # 对话中
    FOLLOWING = "following"          # 跟随


class NPCAI:
    """NPC AI控制器"""
    
    def __init__(self, npc: NPC, combat_engine: Optional[CombatEngine] = None):
        """
        初始化NPC AI
        
        Args:
            npc: NPC对象
            combat_engine: 战斗引擎（可选，用于战斗状态）
        """
        self.npc = npc
        self.state = AIState.IDLE
        self.logger = get_logger(f"NPCAI_{npc.name}")
        
        # 战斗引擎
        self.combat_engine = combat_engine
        
        # AI目标
        self.target_position: Optional[Position] = None
        self.target_entity = None
        
        # AI决策参数
        self.decision_interval = 2.0  # 每2秒重新决策
        self.last_decision_time = 0.0
        
        # 游戏时间（用于战斗冷却）
        self.game_time = 0.0
    
    def update(self, delta_time: float, game_time: float):
        """
        更新AI逻辑
        
        Args:
            delta_time: 时间增量
            game_time: 游戏总时间
        """
        if not self.npc.is_alive:
            return
        
        # 保存游戏时间（用于战斗冷却）
        self.game_time = game_time
        
        # 定期重新决策
        if game_time - self.last_decision_time >= self.decision_interval:
            self.make_decision()
            self.last_decision_time = game_time
        
        # 执行当前状态的行为
        self.execute_state(delta_time, game_time)
    
    def make_decision(self):
        """根据NPC状态和需求做出决策"""
        # 检查基本需求
        if self.npc.needs["food"] < 30:
            self.set_state(AIState.SEEKING_FOOD)
        elif self.npc.needs["rest"] < 20:
            self.set_state(AIState.RESTING)
        elif self.state == AIState.IDLE:
            # 空闲时随机决定做什么
            import random
            rand = random.random()
            if rand < 0.3:
                # 30%概率移动到随机位置（需要世界引用）
                # 这里简化处理，实际应该从游戏引擎获取世界
                pass
        # 根据情绪和个性做决策
        elif self.npc.mood == NPCMood.STRESSED and self.npc.personality.aggression > 70:
            # 压力大且攻击性高的NPC可能变得敌对
            if self.npc.relationship_with_player == NPCRelationship.NEUTRAL:
                self.npc.modify_relationship(-10)
    
    def execute_state(self, delta_time: float, game_time: float = None):
        """
        执行当前状态的行为
        
        Args:
            delta_time: 时间增量
            game_time: 游戏总时间（如果为None，使用self.game_time）
        """
        # 如果没有传入game_time，使用保存的值
        if game_time is None:
            game_time = self.game_time
        
        if self.state == AIState.MOVING:
            # 修复：实际更新NPC位置，而不是只判断距离
            if self.target_position:
                # 计算方向向量
                dx = self.target_position.x - self.npc.position.x
                dy = self.target_position.y - self.npc.position.y
                distance = (dx ** 2 + dy ** 2) ** 0.5
                
                # 防抖动逻辑：如果距离非常近，直接吸附到目标点
                if distance < 1.0:
                    self.npc.position.x = self.target_position.x
                    self.npc.position.y = self.target_position.y
                    self.set_state(AIState.IDLE)
                    self.target_position = None
                elif distance < 5.0:
                    # 已经很接近，直接到达
                    self.npc.position.x = self.target_position.x
                    self.npc.position.y = self.target_position.y
                    self.set_state(AIState.IDLE)
                    self.target_position = None
                else:
                    # 计算移动速度（如果NPC没有speed属性，使用默认值）
                    move_speed = getattr(self.npc, 'current_speed', 50.0)
                    
                    # 归一化方向向量
                    if distance > 0:
                        dx /= distance
                        dy /= distance
                    
                    # 根据delta_time和速度更新位置
                    move_distance = move_speed * delta_time
                    
                    # 确保不会超过目标位置
                    if move_distance >= distance:
                        self.npc.position.x = self.target_position.x
                        self.npc.position.y = self.target_position.y
                        self.set_state(AIState.IDLE)
                        self.target_position = None
                    else:
                        self.npc.position.x += dx * move_distance
                        self.npc.position.y += dy * move_distance
            else:
                # 没有目标位置，切换回空闲状态
                self.set_state(AIState.IDLE)
        
        elif self.state == AIState.SEEKING_FOOD:
            # 寻找食物（简化处理：移动到随机位置）
            if not self.target_position:
                # 这里可以改进为寻找食物源
                self.set_state(AIState.IDLE)
        
        elif self.state == AIState.RESTING:
            # 休息，恢复需求
            self.npc.needs["rest"] = min(100, self.npc.needs["rest"] + 20 * delta_time)
            if self.npc.needs["rest"] >= 80:
                self.set_state(AIState.IDLE)
        
        elif self.state == AIState.COMBAT:
            # 战斗状态：使用新的冷却系统进行攻击
            if not self.combat_engine:
                self.logger.warning(f"{self.npc.name} 处于战斗状态，但未提供战斗引擎，切换为空闲状态")
                self.set_state(AIState.IDLE)
                return
            
            # 检查目标是否有效
            if not self.target_entity:
                self.logger.debug(f"{self.npc.name} 战斗目标丢失，切换为空闲状态")
                self.set_state(AIState.IDLE)
                return
            
            # 检查目标是否存活
            if not hasattr(self.target_entity, 'is_alive') or not self.target_entity.is_alive:
                self.logger.debug(f"{self.npc.name} 的目标已死亡，切换为空闲状态")
                self.target_entity = None
                self.set_state(AIState.IDLE)
                return
            
            # 检查是否在攻击范围内
            weapon = getattr(self.npc, 'equipped_weapon', None)
            can_attack = self.combat_engine.can_attack(self.npc, self.target_entity, weapon)
            
            if not can_attack:
                # 目标超出攻击范围，切换为移动状态追击
                self.logger.debug(f"{self.npc.name} 目标超出攻击范围，开始追击")
                self.target_position = self.target_entity.position
                self.set_state(AIState.MOVING)
                return
            
            # 在攻击范围内，执行战斗回合（包含冷却检查）
            result = self.combat_engine.process_combat_round(
                attacker=self.npc,
                defender=self.target_entity,
                time_current=game_time,
                weapon=weapon
            )
            
            # 处理战斗结果
            if result.attack_succeeded:
                # 攻击成功（通过了冷却检查）
                if result.is_miss:
                    self.logger.debug(f"{self.npc.name} 攻击 {self.target_entity.name} 未命中")
                elif result.is_blocked:
                    self.logger.debug(f"{self.npc.name} 的攻击被 {self.target_entity.name} 格挡")
                elif result.damage_dealt > 0:
                    self.logger.info(f"{self.npc.name} 对 {self.target_entity.name} 造成 {result.damage_dealt} 点伤害" + 
                                   ("（暴击！）" if result.is_critical else ""))
                    
                    # 如果目标死亡，结束战斗
                    if not self.target_entity.is_alive:
                        self.logger.info(f"{self.npc.name} 击败了 {self.target_entity.name}")
                        self.target_entity = None
                        self.set_state(AIState.IDLE)
                else:
                    self.logger.debug(f"{self.npc.name} 对 {self.target_entity.name} 的攻击没有造成伤害")
            else:
                # 攻击冷却中，不做任何事（可以在未来添加防御/移动逻辑）
                pass
    
    def set_state(self, new_state: AIState):
        """
        设置AI状态
        
        Args:
            new_state: 新状态
        """
        if self.state != new_state:
            self.logger.debug(f"{self.npc.name} AI状态变更: {self.state.value} -> {new_state.value}")
            self.state = new_state
            self.npc.ai_state = new_state.value
    
    def move_to(self, target: Position):
        """
        移动到目标位置
        
        Args:
            target: 目标位置
        """
        self.target_position = target
        self.npc.move_to(target)
        self.set_state(AIState.MOVING)
    
    def start_combat(self, target):
        """
        开始战斗
        
        Args:
            target: 目标实体
        """
        self.target_entity = target
        self.set_state(AIState.COMBAT)
    
    def generate_response(self, player_message: str) -> str:
        """
        生成对话响应（基础版本，后续可用OpenAI增强）
        
        Args:
            player_message: 玩家消息
            
        Returns:
            NPC响应
        """
        # 基础响应逻辑（后续由OpenAI替换）
        if "你好" in player_message or "hello" in player_message.lower():
            return f"你好，我是{self.npc.name}。"
        elif "任务" in player_message or "quest" in player_message.lower():
            return "我现在没有任务给你。"
        else:
            # 根据个性生成简单响应
            if self.npc.personality.kindness > 70:
                return "很高兴见到你！"
            elif self.npc.personality.aggression > 70:
                return "你想干什么？"
            else:
                return "嗯..."

