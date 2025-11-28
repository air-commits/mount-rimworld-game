"""
配置管理模块
负责加载和管理游戏配置文件
"""

import json
import os
from typing import Any, Dict


class Config:
    """游戏配置管理器"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """从文件加载配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                self._config = {}
        else:
            print(f"配置文件不存在: {self.config_path}")
            self._config = {}
    
    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的嵌套键，如 'game.name'）
        
        Args:
            key: 配置键，支持嵌套访问（如 'game.name'）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        设置配置值（支持点号分隔的嵌套键）
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        # 导航到嵌套字典
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()


# 全局配置实例
_game_config = None

def get_config(config_path: str = "config.json") -> Config:
    """
    获取全局配置实例（单例模式）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Config实例
    """
    global _game_config
    if _game_config is None:
        _game_config = Config(config_path)
    return _game_config

