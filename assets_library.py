"""
素材库模块
====================
用于存储和管理游戏中的素材资源

【设计说明】
- 集中管理所有游戏素材资源（图片、音频等）
- 存储地图素材路径（地板、地形等）
- 存储NPC素材路径（不同NPC的图片）
- 存储角色素材路径（玩家角色图片）
- 存储地点素材路径（城镇、村庄图标）
- 如果没有素材，游戏会使用默认图形代替（黑色方块）

【使用方式】
1. 创建 AssetsLibrary 实例
2. 使用 add_*_asset() 方法添加素材路径
3. 使用 get_*_asset() 方法获取素材路径
4. 在渲染时检查素材是否存在，不存在则使用默认图形
"""

from typing import Dict, Optional
from utils.logger import get_logger


class AssetsLibrary:
    """
    素材库类
    ====================
    管理游戏中的所有素材资源
    """
    
    def __init__(self):
        """
        初始化素材库
        
        【功能说明】
        - 创建空的素材字典
        - 初始化日志记录器
        - 素材路径可以在运行时动态添加
        """
        self.logger = get_logger("AssetsLibrary")
        
        # 地图素材路径字典（key: 素材名称, value: 文件路径）
        # 例如：{"floor": "assets/map/floor.png"}
        self.map_assets: Dict[str, str] = {}
        
        # NPC素材路径字典（key: NPC名称, value: 文件路径）
        # 例如：{"中立NPC": "assets/npc/neutral.png"}
        self.npc_assets: Dict[str, str] = {}
        
        # 角色素材路径字典（key: 角色名称, value: 文件路径）
        # 例如：{"player": "assets/character/player.png"}
        self.character_assets: Dict[str, str] = {}
        
        # 地点素材路径字典（key: 地点名称, value: 文件路径）
        # 例如：{"城镇": "assets/location/town.png"}
        self.location_assets: Dict[str, str] = {}
        
        self.logger.info("素材库初始化完成")
    
    def add_map_asset(self, name: str, path: str):
        """
        添加地图素材路径
        
        Args:
            name: 素材名称（如 "floor", "grass"）
            path: 素材文件路径（相对或绝对路径）
        
        示例：
            assets.add_map_asset("floor", "assets/map/floor.png")
        """
        self.map_assets[name] = path
        self.logger.debug(f"添加地图素材: {name} -> {path}")
    
    def add_npc_asset(self, name: str, path: str):
        """
        添加NPC素材路径
        
        Args:
            name: NPC名称（如 "中立NPC", "友好NPC"）
            path: 素材文件路径
        
        示例：
            assets.add_npc_asset("中立NPC", "assets/npc/neutral.png")
        """
        self.npc_assets[name] = path
        self.logger.debug(f"添加NPC素材: {name} -> {path}")
    
    def add_character_asset(self, name: str, path: str):
        """
        添加角色素材路径
        
        Args:
            name: 角色名称（如 "player"）
            path: 素材文件路径
        
        示例：
            assets.add_character_asset("player", "assets/character/player.png")
        """
        self.character_assets[name] = path
        self.logger.debug(f"添加角色素材: {name} -> {path}")
    
    def add_location_asset(self, name: str, path: str):
        """
        添加地点素材路径
        
        Args:
            name: 地点名称（如 "城镇", "村庄"）
            path: 素材文件路径
        
        示例：
            assets.add_location_asset("城镇", "assets/location/town.png")
        """
        self.location_assets[name] = path
        self.logger.debug(f"添加地点素材: {name} -> {path}")
    
    def get_map_asset(self, name: str) -> Optional[str]:
        """
        获取地图素材路径
        
        Args:
            name: 素材名称
        
        Returns:
            Optional[str]: 素材文件路径，如果不存在返回None
        """
        return self.map_assets.get(name)
    
    def get_npc_asset(self, name: str) -> Optional[str]:
        """
        获取NPC素材路径
        
        Args:
            name: NPC名称
        
        Returns:
            Optional[str]: 素材文件路径，如果不存在返回None
        """
        return self.npc_assets.get(name)
    
    def get_character_asset(self, name: str) -> Optional[str]:
        """
        获取角色素材路径
        
        Args:
            name: 角色名称
        
        Returns:
            Optional[str]: 素材文件路径，如果不存在返回None
        """
        return self.character_assets.get(name)
    
    def get_location_asset(self, name: str) -> Optional[str]:
        """
        获取地点素材路径
        
        Args:
            name: 地点名称
        
        Returns:
            Optional[str]: 素材文件路径，如果不存在返回None
        """
        return self.location_assets.get(name)
