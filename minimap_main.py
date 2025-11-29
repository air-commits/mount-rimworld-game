"""
小地图独立主程序
====================
独立的小地图界面，可以返回主main

【设计说明】
- 这是一个独立的小地图界面
- 目前是空地图，等待后续添加功能
- 可以返回主main
"""

import pygame
import os
from typing import Dict, Any, Optional
from base_main import BaseMain


class MinimapMain(BaseMain):
    """
    小地图主程序类
    ====================
    独立的小地图界面
    """
    
    def __init__(self, saved_state: Optional[Dict[str, Any]] = None):
        """
        初始化小地图主程序
        
        Args:
            saved_state: 保存的游戏状态（可选）
        """
        super().__init__("小地图", saved_state)
        
        # 小地图特有的颜色
        self.colors['grass'] = (34, 139, 34)
        self.colors['button'] = (100, 150, 200)
    
    def draw(self):
        """绘制界面（重写基类方法以添加小地图特有内容）"""
        # 调用基类的默认绘制（背景 + 标题 + 提示）
        super().draw()
        
        # 绘制空地图（全部为草地）
        map_x = 50
        map_y = 50
        map_width = self.width - 100
        map_height = self.height - 150
        
        # 地图背景（草地色）
        pygame.draw.rect(self.screen, self.colors['grass'],
                        (map_x, map_y, map_width, map_height))
        pygame.draw.rect(self.screen, self.colors['border'],
                        (map_x, map_y, map_width, map_height), 2)


def main():
    """主函数"""
    minimap = MinimapMain()
    result = minimap.run()
    pygame.quit()
    return result


if __name__ == "__main__":
    main()

