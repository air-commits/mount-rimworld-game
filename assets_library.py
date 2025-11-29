"""
素材库模块
====================
用于存储和管理游戏中的素材资源

【设计说明】
- 存储地图素材路径
- 存储NPC素材路径
- 存储角色素材路径
- 如果没有素材，使用默认图形代替
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
        """初始化素材库"""
        self.logger = get_logger("AssetsLibrary")
        
        # 地图素材路径（待添加）
        self.map_assets: Dict[str, str] = {}
        
        # NPC素材路径（待添加）
        self.npc_assets: Dict[str, str] = {}
        
        # 角色素材路径（待添加）
        self.character_assets: Dict[str, str] = {}
        
        # 城镇/村庄素材路径（待添加）
        self.location_assets: Dict[str, str] = {}
        
        self.logger.info("素材库初始化完成")
    
    def add_map_asset(self, name: str, path: str):
        """添加地图素材"""
        self.map_assets[name] = path
        self.logger.debug(f"添加地图素材: {name} -> {path}")
    
    def add_npc_asset(self, name: str, path: str):
        """添加NPC素材"""
        self.npc_assets[name] = path
        self.logger.debug(f"添加NPC素材: {name} -> {path}")
    
    def add_character_asset(self, name: str, path: str):
        """添加角色素材"""
        self.character_assets[name] = path
        self.logger.debug(f"添加角色素材: {name} -> {path}")
    
    def add_location_asset(self, name: str, path: str):
        """添加地点素材"""
        self.location_assets[name] = path
        self.logger.debug(f"添加地点素材: {name} -> {path}")
    
    def get_map_asset(self, name: str) -> Optional[str]:
        """获取地图素材路径"""
        return self.map_assets.get(name)
    
    def get_npc_asset(self, name: str) -> Optional[str]:
        """获取NPC素材路径"""
        return self.npc_assets.get(name)
    
    def get_character_asset(self, name: str) -> Optional[str]:
        """获取角色素材路径"""
        return self.character_assets.get(name)
    
    def get_location_asset(self, name: str) -> Optional[str]:
        """获取地点素材路径"""
        return self.location_assets.get(name)
