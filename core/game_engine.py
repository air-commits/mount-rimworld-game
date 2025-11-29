"""
游戏引擎
游戏的核心循环和系统管理
"""

import time
from typing import Optional, List

from core.world import World, Position
from core.game_state import GameState, GameStateType
from utils.logger import get_logger
from utils.config import get_config


class GameEngine:
    """游戏主引擎"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化游戏引擎
        
        Args:
            config_path: 配置文件路径
        """
        self.logger = get_logger("GameEngine")
        self.config = get_config(config_path)
        
        # 初始化核心系统
        world_width = self.config.get("world.width", 1000)
        world_height = self.config.get("world.height", 1000)
        tile_size = self.config.get("world.tile_size", 32)
        self.logger.info(f"[世界] 创建游戏世界 - 尺寸: {world_width}x{world_height}, 瓦片大小: {tile_size}")
        
        self.world = World(
            width=world_width,
            height=world_height,
            tile_size=tile_size
        )
        self.logger.info(f"[世界] 世界创建完成 - 地形网格: {len(self.world.terrain_grid)}x{len(self.world.terrain_grid[0]) if self.world.terrain_grid else 0}")
        
        self.game_state = GameState()
        
        # 游戏循环控制
        self.running = False
        self.fps = self.config.get("game.fps", 60)
        self.frame_time = 1.0 / self.fps
        
        # 游戏时间
        self.game_time = 0.0
        self.time_scale = self.config.get("world.time_scale", 1.0)
        
        # 实体列表（后续添加）
        self.entities = []
        
        self.logger.info("游戏引擎初始化完成")
    
    def start(self):
        """
        启动游戏引擎（仅用于命令行模式）
        注意：GUI模式不应调用此方法，应直接调用update()方法
        """
        self.running = True
        self.game_state.change_state(GameStateType.PLAYING)
        self.logger.info("游戏引擎启动（命令行模式）")
        self.main_loop()
    
    def stop(self):
        """停止游戏引擎"""
        self.running = False
        self.logger.info("游戏引擎停止")
    
    def main_loop(self):
        """
        游戏主循环（仅用于命令行模式）
        注意：GUI模式应使用外部循环，直接调用update()方法
        """
        last_time = time.time()
        accumulator = 0.0
        
        while self.running:
            current_time = time.time()
            delta_time = min(current_time - last_time, 0.25)  # 限制最大时间步长
            last_time = current_time
            
            # 更新游戏时间
            self.game_time += delta_time * self.time_scale
            
            # 固定时间步长更新（物理和游戏逻辑）
            accumulator += delta_time
            fixed_delta = self.frame_time
            while accumulator >= fixed_delta:
                self.update(fixed_delta)
                accumulator -= fixed_delta
            
            # 渲染（如果有图形界面）
            # self.render()
            
            # 控制帧率（仅命令行模式使用）
            elapsed = time.time() - current_time
            sleep_time = max(0, self.frame_time - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def update(self, delta_time: float):
        """
        更新游戏逻辑
        
        Args:
            delta_time: 时间增量（秒）
        """
        # 根据当前状态更新
        if self.game_state.is_state(GameStateType.PLAYING):
            self.update_gameplay(delta_time)
        elif self.game_state.is_state(GameStateType.COMBAT):
            self.update_combat(delta_time)
        elif self.game_state.is_state(GameStateType.PAUSED):
            pass  # 暂停时不更新
    
    def update_gameplay(self, delta_time: float):
        """
        更新游戏玩法逻辑
        
        Args:
            delta_time: 时间增量
        """
        self.logger.debug(f"[引擎] 更新游戏逻辑 - 时间增量: {delta_time:.3f}s, 实体数量: {len(self.entities)}, 游戏时间: {self.game_time:.1f}s")
        
        # 更新所有实体
        for entity in self.entities:
            if hasattr(entity, 'update'):
                entity.update(delta_time)
    
    def update_combat(self, delta_time: float):
        """
        更新战斗逻辑
        
        Args:
            delta_time: 时间增量
        """
        # 战斗系统更新（后续实现）
        pass
    
    def add_entity(self, entity):
        """
        添加实体到世界
        
        Args:
            entity: 实体对象
        """
        self.entities.append(entity)
        entity_name = getattr(entity, 'name', 'Unknown')
        entity_pos = getattr(entity, 'position', None)
        pos_str = f"({entity_pos.x:.1f}, {entity_pos.y:.1f})" if entity_pos else "Unknown"
        self.logger.info(f"[实体] 添加实体到世界 - 类型: {type(entity).__name__}, 名称: {entity_name}, 位置: {pos_str}, 总实体数: {len(self.entities)}")
    
    def remove_entity(self, entity):
        """
        从世界移除实体
        
        Args:
            entity: 实体对象
        """
        if entity in self.entities:
            self.entities.remove(entity)
            self.logger.debug(f"移除实体: {type(entity).__name__}")
    
    def get_entities_in_range(self, position: Position, radius: float) -> List:
        """
        获取指定位置和半径范围内的实体（用于优化战斗和AI索敌）
        
        Args:
            position: 中心位置
            radius: 搜索半径
            
        Returns:
            范围内的实体列表
        """
        entities_in_range = []
        radius_sq = radius ** 2  # 使用平方距离比较，避免开方运算
        
        for entity in self.entities:
            if not hasattr(entity, 'position'):
                continue
            
            # 计算平方距离
            dx = entity.position.x - position.x
            dy = entity.position.y - position.y
            dist_sq = dx ** 2 + dy ** 2
            
            # 使用平方距离比较
            if dist_sq <= radius_sq:
                entities_in_range.append(entity)
        
        return entities_in_range
    
    def get_entities_by_type(self, entity_type):
        """
        根据类型获取实体
        
        Args:
            entity_type: 实体类型（类）
            
        Returns:
            指定类型的实体列表
        """
        return [entity for entity in self.entities if isinstance(entity, entity_type)]

