# 快速开始指南

本指南将帮助你快速上手骑砍环世界融合游戏。

## 第一步：安装依赖

```bash
cd mount_rimworld_game
pip install -r requirements.txt
```

注意：如果需要使用OpenAI集成功能，还需要安装：
```bash
pip install requests
```

## 第二步：运行游戏

```bash
python main.py
```

游戏会启动一个演示模式，展示各个系统的功能。

## 第三步：了解基本概念

### 角色系统

游戏中有两种主要角色类型：

1. **玩家角色 (Player)**
   - 可以控制的角色
   - 有金币、声望等属性
   - 可以升级和学习技能

2. **NPC (Non-Player Character)**
   - 由AI控制的角色
   - 有独特的个性特征
   - 有需求系统（食物、休息等）
   - 可以与玩家建立关系

### 战斗系统

- 支持多种武器类型（剑、弓、长矛等）
- 伤害计算考虑角色属性和武器
- 有暴击和未命中机制
- 支持技能加成

### 基地系统

- **资源管理**: 食物、木材、石头、金属等
- **建筑系统**: 可以建造各种建筑
- **生产系统**: 通过配方制作物品和资源

## 第四步：配置游戏

编辑 `config.json` 可以调整游戏参数：

- 世界大小
- 战斗参数
- 基地初始资源
- OpenAI集成设置

## 第五步：编写自己的游戏逻辑

### 创建自定义NPC

```python
from entities.npc import NPC, NPCPersonality
from core.world import Position

npc = NPC(
    name="自定义NPC",
    position=Position(300, 300),
    personality=NPCPersonality(
        traits=["brave", "loyal"],
        kindness=70,
        aggression=60,
        profession="warrior"
    )
)
```

### 创建战斗

```python
from combat.combat_engine import CombatEngine
from combat.weapons import get_weapon

combat = CombatEngine()
attacker.equipped_weapon = get_weapon("iron_sword")

if combat.can_attack(attacker, defender):
    result = combat.calculate_attack(attacker, defender, attacker.equipped_weapon)
    print(result)
```

### 管理基地资源

```python
from colony.resource import ResourceManager, ResourceType

# 创建资源管理器
resources = ResourceManager({
    ResourceType.FOOD: 100,
    ResourceType.WOOD: 50
})

# 添加资源
resources.add_resource(ResourceType.FOOD, 20)

# 检查资源
if resources.has_enough(ResourceType.WOOD, 30):
    resources.remove_resource(ResourceType.WOOD, 30)
    print("资源足够，已扣除")
```

### 建造建筑

```python
from colony.building import Building, BuildingType, BuildingManager
from core.world import Position

building_manager = BuildingManager()

# 创建建筑
farm = Building(
    building_type=BuildingType.FARM,
    position=Position(400, 400)
)

# 添加到管理器
building_manager.add_building(farm)

# 完成建造
farm.complete()
```

## 下一步

- 阅读 [README.md](../README.md) 了解完整的项目结构
- 查看 [OPENAI_SETUP.md](./OPENAI_SETUP.md) 学习如何配置OpenAI集成
- 探索源代码，了解各个系统的实现细节

## 常见问题

**Q: 游戏没有图形界面吗？**
A: 当前版本专注于游戏逻辑，没有图形界面。你可以使用pygame等库添加图形界面。

**Q: 如何启用OpenAI功能？**
A: 参考 [OPENAI_SETUP.md](./OPENAI_SETUP.md) 文档。

**Q: 如何保存游戏？**
A: 存档系统尚未实现，这是未来的功能。

**Q: 可以添加新的武器/建筑吗？**
A: 可以！查看README中的"扩展开发"部分。

## 获取帮助

- 查看代码注释（所有代码都有详细的中文注释）
- 阅读源代码了解实现细节
- 提交Issue报告问题或建议功能

