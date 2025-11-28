"""
日志系统
提供统一的日志记录功能
"""

import logging
import os
from datetime import datetime


class Logger:
    """游戏日志记录器"""
    
    def __init__(self, name: str = "GameLogger", log_dir: str = "logs"):
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称
            log_dir: 日志文件保存目录
        """
        self.name = name
        self.log_dir = log_dir
        
        # 创建日志目录
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 创建日志记录器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)
            
            # 文件处理器
            log_file = os.path.join(
                log_dir, 
                f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            )
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """记录调试信息"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """记录一般信息"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """记录警告信息"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录错误信息"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """记录严重错误信息"""
        self.logger.critical(message)


# 全局日志实例
_game_logger = None

def get_logger(name: str = "GameLogger") -> Logger:
    """
    获取全局日志实例（单例模式）
    
    Args:
        name: 日志记录器名称
        
    Returns:
        Logger实例
    """
    global _game_logger
    if _game_logger is None:
        _game_logger = Logger(name)
    return _game_logger

