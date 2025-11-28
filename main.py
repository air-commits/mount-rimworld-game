"""
游戏主入口
骑砍环世界融合游戏

这个文件保留作为演示模式入口。
要运行完整游戏，请使用: python game.py
"""

import sys
import os

# 添加项目根目录到Python路径
_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

# 现在可以使用绝对导入
from core.game_engine import GameEngine
from core.world import Position
from entities.player import Player
from entities.npc import NPC, NPCPersonality
from colony.resource import ResourceManager, ResourceType
from colony.building import BuildingManager, Building, BuildingType
from colony.production import ProductionSystem
from combat.weapons import get_weapon
from combat.combat_engine import CombatEngine
from ai.npc_ai import NPCAI
from ai.openai_integration import get_openai_integration
from utils.logger import get_logger
from utils.config import get_config


def create_test_world(engine: GameEngine):
    """
    创建测试游戏世界（用于演示）
    
    Args:
        engine: 游戏引擎实例
    """
    logger = get_logger("GameSetup")
    logger.info("初始化测试世界...")
    
    # 创建战斗引擎（用于NPC AI）
    combat_engine = CombatEngine()
    
    # 创建玩家
    player = Player(name="玩家", position=Position(500, 500))
    engine.add_entity(player)
    
    # 创建几个NPC
    npcs = [
        NPC(
            name="村民A",
            position=Position(600, 500),
            personality=NPCPersonality(
                traits=["kind", "helpful"],
                kindness=80,
                profession="farmer"
            )
        ),
        NPC(
            name="守卫B",
            position=Position(700, 500),
            personality=NPCPersonality(
                traits=["brave", "loyal"],
                aggression=60,
                loyalty=90,
                profession="guard"
            )
        ),
        NPC(
            name="商人C",
            position=Position(400, 500),
            personality=NPCPersonality(
                traits=["greedy", "clever"],
                kindness=40,
                profession="merchant"
            )
        ),
    ]
    
    for npc in npcs:
        engine.add_entity(npc)
        # 为NPC添加AI（传入战斗引擎）
        npc_ai = NPCAI(npc, combat_engine=combat_engine)
        # 这里可以将AI添加到引擎管理，暂时简化处理
    
    # 创建基地资源管理器
    resource_manager = ResourceManager({
        ResourceType.FOOD: 100,
        ResourceType.WOOD: 100,
        ResourceType.STONE: 50,
        ResourceType.METAL: 25
    })
    
    # 创建生产系统
    production_system = ProductionSystem(resource_manager)
    
    # 创建建筑管理器
    building_manager = BuildingManager()
    
    logger.info("测试世界创建完成")
    
    return {
        "player": player,
        "npcs": npcs,
        "resource_manager": resource_manager,
        "production_system": production_system,
        "building_manager": building_manager
    }


def main():
    """游戏主函数"""
    logger = get_logger("Main")
    logger.info("=" * 50)
    logger.info("骑砍环世界融合游戏启动")
    logger.info("=" * 50)
    
    try:
        # 初始化游戏引擎
        engine = GameEngine(config_path="config.json")
        
        # 创建测试世界
        game_world = create_test_world(engine)
        player = game_world["player"]
        
        # 显示游戏信息
        print("\n" + "=" * 50)
        print("游戏已启动！")
        print("=" * 50)
        print(f"玩家: {player}")
        print(f"世界大小: {engine.world.width} x {engine.world.height}")
        print(f"NPC数量: {len(game_world['npcs'])}")
        
        # 检查OpenAI集成
        openai_integration = get_openai_integration()
        if openai_integration.enabled:
            print("\n✓ OpenAI集成已启用")
        else:
            print("\n○ OpenAI集成已禁用（可在config.json中启用）")
        
        # 演示功能
        print("\n" + "-" * 50)
        print("功能演示:")
        print("-" * 50)
        
        # 演示资源系统
        resource_manager = game_world["resource_manager"]
        print("\n初始资源:")
        print(resource_manager)
        
        # 演示NPC对话（如果OpenAI可用）
        npc = game_world["npcs"][0]
        print(f"\n与 {npc.name} 对话:")
        player_message = "你好"
        response = openai_integration.generate_npc_response(npc, player_message)
        print(f"玩家: {player_message}")
        print(f"{npc.name}: {response}")
        
        # 演示战斗系统（使用已有的战斗引擎）
        # 注意：combat_engine已在create_test_world中创建，这里为了演示需要再次创建
        combat_engine = CombatEngine()
        
        print("\n战斗系统演示:")
        attacker = game_world["npcs"][0]
        defender = game_world["npcs"][1]
        
        # 给攻击者装备武器
        weapon = get_weapon("iron_sword")
        if weapon:
            attacker.equipped_weapon = weapon
        
        # 执行一次攻击
        if combat_engine.can_attack(attacker, defender, weapon):
            result = combat_engine.calculate_attack(attacker, defender, weapon)
            print(result)
            print(f"{defender.name} 当前生命值: {defender.current_health}/{defender.max_health}")
        
        print("\n" + "=" * 50)
        print("游戏系统运行正常！")
        print("=" * 50)
        
        # 注意：实际游戏循环需要图形界面或命令行界面
        # 这里只演示系统初始化
        print("\n提示: 当前为系统演示模式。")
        print("要运行完整的交互式游戏，请使用: python game.py")
        
    except KeyboardInterrupt:
        logger.info("游戏被用户中断")
    except Exception as e:
        logger.error(f"游戏运行出错: {e}", exc_info=True)
        print(f"\n错误: {e}")
        print("请检查日志文件获取详细信息。")
    
    logger.info("游戏结束")


if __name__ == "__main__":
    main()

