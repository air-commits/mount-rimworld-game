"""
实体系统模块
包含角色、玩家、NPC等游戏实体
"""

from entities.character import Character, CharacterStats
from entities.player import Player
from entities.npc import NPC, NPCPersonality

__all__ = ['Character', 'CharacterStats', 'Player', 'NPC', 'NPCPersonality']

