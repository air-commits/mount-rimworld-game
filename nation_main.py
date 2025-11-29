"""
国家界面主程序
====================
独立的国家界面，可以返回主main
"""

from typing import Dict, Any, Optional
from base_main import BaseMain


class NationMain(BaseMain):
    """国家界面主程序类"""
    
    def __init__(self, saved_state: Optional[Dict[str, Any]] = None):
        super().__init__("国家", saved_state)

