"""
军队界面主程序
====================
独立的军队界面，可以返回主main
"""

from typing import Dict, Any, Optional
from base_main import BaseMain


class ArmyMain(BaseMain):
    """军队界面主程序类"""
    
    def __init__(self, saved_state: Optional[Dict[str, Any]] = None):
        super().__init__("军队", saved_state)

