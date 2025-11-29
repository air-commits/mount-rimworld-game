"""
界面主程序基类
====================
所有独立界面主程序的基类，提供通用功能
"""

import sys
import os
import pygame
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    from utils.logger import get_logger
except ImportError:
    # 如果导入失败，创建一个简单的logger
    import logging
    def get_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger


class BaseMain:
    """
    界面主程序基类
    ====================
    提供所有界面主程序的通用功能：
    - 字体加载（支持中文）
    - 事件处理
    - 基本绘制
    """
    
    def __init__(self, title: str, saved_state: Optional[Dict[str, Any]] = None):
        """
        初始化界面主程序
        
        Args:
            title: 界面标题（用于窗口标题和日志）
            saved_state: 保存的游戏状态（可选）
        """
        self.logger = get_logger(f"{title}Main")
        self.title = title
        self.saved_state = saved_state or {}
        
        # 初始化Pygame（如果尚未初始化）
        if not pygame.get_init():
            pygame.init()
        
        # 窗口设置
        self.width = 1024
        self.height = 768
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(title)
        
        # 字体（支持中文）
        self.font_small = self._load_font(24)
        self.font_medium = self._load_font(32)
        self.font_large = self._load_font(48)
        
        # 颜色配置
        self.colors = {
            'bg': (40, 40, 40),
            'panel': (60, 60, 60),
            'text': (255, 255, 255),
            'border': (200, 200, 200),
            'hint': (180, 180, 180),
        }
        
        # 界面状态
        self.running = True
        
        self.logger.info(f"{title}界面初始化完成")
    
    def _load_font(self, size: int):
        """
        加载字体（支持中文）
        
        Args:
            size: 字体大小
            
        Returns:
            Font对象
        """
        # 优先尝试系统常用中文字体
        chinese_fonts = [
            'simhei',           # 黑体（Windows/Linux常见）
            'microsoftyahei',    # 微软雅黑（Windows）
            'simsun',           # 宋体（Windows）
            'PingFang SC',      # 苹方（macOS）
            'WenQuanYi Micro Hei',  # 文泉驿微米黑（Linux）
        ]
        
        for font_name in chinese_fonts:
            try:
                font = pygame.font.SysFont(font_name, size)
                # 测试字体是否支持中文
                test_surface = font.render('中', True, (255, 255, 255))
                if test_surface.get_width() > 0:
                    self.logger.debug(f"成功加载中文字体: {font_name} (大小: {size})")
                    return font
            except Exception as e:
                self.logger.debug(f"尝试加载字体 {font_name} 失败: {e}")
                continue
        
        # 尝试加载本地字体文件
        local_paths = ['assets/font.ttf', 'font.ttf']
        for path in local_paths:
            try:
                if os.path.exists(path):
                    font = pygame.font.Font(path, size)
                    self.logger.info(f"成功加载本地字体文件: {path} (大小: {size})")
                    return font
            except Exception as e:
                self.logger.debug(f"尝试加载本地字体 {path} 失败: {e}")
                continue
        
        # 保底方案：使用默认字体（可能不支持中文）
        self.logger.warning(f"未能加载中文字体，使用默认字体（可能不支持中文显示）")
        return pygame.font.Font(None, size)
    
    def handle_events(self):
        """
        处理事件（子类可以重写以添加自定义事件处理）
        
        Returns:
            bool: 是否继续运行
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # ESC键：返回主main
                    self.running = False
                    return False
        
        return True
    
    def draw(self):
        """
        绘制界面（子类必须重写此方法）
        """
        # 默认绘制：背景 + 标题 + 提示
        self.screen.fill(self.colors['bg'])
        
        # 标题
        title = self.font_large.render(self.title, True, self.colors['text'])
        title_rect = title.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title, title_rect)
        
        # 提示文字
        hint = "按ESC返回主地图"
        hint_text = self.font_small.render(hint, True, self.colors['hint'])
        hint_rect = hint_text.get_rect(center=(self.width // 2, self.height - 50))
        self.screen.blit(hint_text, hint_rect)
    
    def run(self) -> Dict[str, Any]:
        """
        运行界面主程序
        
        Returns:
            返回更新后的游戏状态
        """
        self.logger.info(f"开始运行{self.title}界面")
        clock = pygame.time.Clock()
        
        while self.running:
            # 处理事件
            if not self.handle_events():
                break
            
            # 绘制
            self.draw()
            pygame.display.flip()
            clock.tick(60)
        
        # 返回保存的状态
        self.logger.info(f"{self.title}界面结束，返回主main")
        return self.saved_state

