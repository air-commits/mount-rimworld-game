"""
游戏状态管理
管理游戏的各种状态（运行、暂停、菜单等）
"""

from enum import Enum
from typing import Dict, Any


class GameStateType(Enum):
    """游戏状态类型"""
    MENU = "menu"              # 主菜单
    PLAYING = "playing"        # 游戏中
    PAUSED = "paused"          # 暂停
    INVENTORY = "inventory"    # 背包界面
    COLONY = "colony"          # 基地管理界面
    DIALOG = "dialog"          # 对话界面
    COMBAT = "combat"          # 战斗状态
    GAME_OVER = "game_over"    # 游戏结束


class GameState:
    """游戏状态管理器"""
    
    def __init__(self):
        """初始化游戏状态"""
        self.current_state: GameStateType = GameStateType.MENU
        self.previous_state: GameStateType = GameStateType.MENU
        self.state_data: Dict[str, Any] = {}  # 状态相关数据
    
    def change_state(self, new_state: GameStateType, data: Dict[str, Any] = None):
        """
        切换游戏状态
        
        Args:
            new_state: 新状态
            data: 状态相关数据
        """
        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_data = data or {}
    
    def push_state(self, new_state: GameStateType, data: Dict[str, Any] = None):
        """
        推入新状态（保留当前状态，可以返回）
        
        Args:
            new_state: 新状态
            data: 状态相关数据
        """
        self.change_state(new_state, data)
    
    def pop_state(self):
        """返回到上一个状态"""
        if self.previous_state:
            self.current_state, self.previous_state = \
                self.previous_state, self.current_state
    
    def is_state(self, state: GameStateType) -> bool:
        """
        检查当前是否为指定状态
        
        Args:
            state: 要检查的状态
            
        Returns:
            是否为指定状态
        """
        return self.current_state == state
    
    def get_state_data(self, key: str, default: Any = None) -> Any:
        """
        获取状态数据
        
        Args:
            key: 数据键
            default: 默认值
            
        Returns:
            状态数据值
        """
        return self.state_data.get(key, default)

