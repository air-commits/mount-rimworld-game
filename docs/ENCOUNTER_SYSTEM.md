# 遭遇战系统实现文档

## 概述

本系统实现了大地图上的遭遇战功能，当玩家在大地图上与NPC军团接触时，根据NPC的势力关系触发不同的交互：

- **敌对NPC**（faction = 'enemy' 或 'bandit'）：自动触发战斗，切换到战斗场景
- **中立/友善NPC**（faction = 'neutral' 或 'alliance'）：显示交互对话框，提供"交谈/交易/攻击"选项

## 功能特性

### 1. 碰撞检测

在大地图模式下，系统会持续检测玩家与NPC的距离：

- **检测半径**：20像素
- **性能优化**：使用平方距离比较，避免开方运算
- **触发频率**：每次移动后检测，一次只处理一个遭遇

### 2. 敌对遭遇战

当玩家与敌对NPC（`faction` 为 `'enemy'` 或 `'bandit'`）接触时：

1. **自动触发战斗**：立即切换到战斗场景
2. **生成战场地图**：
   - 地图大小：1500x1500像素
   - 地形：主要是草地，10%的区域为森林（障碍物）
   - 避免在起始位置附近放置障碍物
3. **位置设置**：
   - 玩家：左下角（100, height-100）
   - 敌人：右上角（width-100, 100）
4. **战斗提示**：显示红色消息"遭遇敌军！XXX - 战斗开始！"，持续3秒
5. **AI激活**：敌人的AI自动进入战斗状态，开始攻击玩家

### 3. 中立NPC交互

当玩家与中立/友善NPC接触时：

1. **显示交互对话框**：
   - 选项1：交谈
   - 选项2：交易（暂未实现）
   - 选项3：攻击
2. **防止重复触发**：使用 `_encounter_triggered` 标记，确保每次接触只触发一次
3. **用户选择**：按数字键1-3选择对应选项，按ESC取消

### 4. 战斗结束处理

战斗场景中，系统会检测战斗结束条件：

- **玩家死亡**：2秒后自动返回大地图
- **敌人死亡**：2秒后自动返回大地图
- **手动退出**：按TAB键可以提前结束战斗（返回大地图）

战斗结束后：
- 恢复战斗前的大地图
- 恢复玩家位置
- 如果敌人死亡，从世界中移除
- 如果敌人存活，可以恢复其位置（可选）

## 代码结构

### 新增/修改的方法

#### `_check_npc_encounters()`
- 检测玩家与NPC的碰撞
- 根据NPC的faction判断交互方式
- 触发战斗或显示对话框

#### `enter_combat_encounter(enemy_npc)`
- 进入战斗场景
- 生成战场地图
- 设置玩家和敌人位置
- 激活敌人AI

#### `_generate_battlefield()`
- 生成随机战斗地图
- 主要是草地，少量森林障碍物
- 避免在起始位置放置障碍物

#### `exit_combat_encounter()`
- 退出战斗场景
- 恢复大地图状态
- 清理战斗相关属性

#### `show_npc_encounter_dialog(npc)`
- 显示中立NPC交互对话框
- 等待用户选择

#### `handle_npc_encounter_choice(choice)`
- 处理用户选择
- 执行对应操作（交谈/交易/攻击）

### 修改的类属性

#### `NPC` 类
- 新增 `faction` 属性：`'neutral'`, `'enemy'`, `'bandit'`, `'alliance'` 等

#### `GameGUI` 类
- 新增战斗相关属性：
  - `_pre_combat_world`：保存战斗前的大地图
  - `_pre_combat_player_pos`：保存战斗前玩家位置
  - `_combat_enemy`：战斗中的敌人
  - `_combat_message`：战斗提示消息
  - `_combat_message_timer`：消息显示计时器
  - `_combat_end_timer`：战斗结束延迟计时器

## 使用示例

### 创建敌对NPC

```python
from entities.npc import NPC, NPCPersonality

# 创建盗贼
bandit = NPC(
    name="盗贼团",
    position=Position(900, 600),
    personality=NPCPersonality(
        traits=["aggressive", "cruel"],
        aggression=90,
        profession="bandit"
    )
)
bandit.faction = "bandit"  # 设置为敌对

# 创建敌军
enemy = NPC(
    name="敌军斥候",
    position=Position(1100, 800),
    personality=NPCPersonality(
        traits=["hostile", "wary"],
        aggression=80,
        profession="soldier"
    )
)
enemy.faction = "enemy"  # 设置为敌军
```

### 创建中立NPC

```python
# 创建村民（默认faction为'neutral'）
villager = NPC(
    name="村民",
    position=Position(600, 500),
    personality=NPCPersonality(
        traits=["kind", "helpful"],
        kindness=80
    )
)
# 不设置faction，默认为'neutral'
```

## 交互流程

### 敌对遭遇流程

```
玩家移动
  ↓
检测到敌对NPC（距离<20像素）
  ↓
enter_combat_encounter()
  ↓
生成战场地图
  ↓
切换到战斗场景
  ↓
显示战斗提示
  ↓
开始战斗
  ↓
战斗结束（玩家或敌人死亡）
  ↓
延迟2秒
  ↓
exit_combat_encounter()
  ↓
返回大地图
```

### 中立NPC交互流程

```
玩家移动
  ↓
检测到中立NPC（距离<20像素）
  ↓
show_npc_encounter_dialog()
  ↓
显示交互选项
  ↓
用户选择（1/2/3）
  ↓
handle_npc_encounter_choice()
  ↓
执行对应操作：
  - 1: 交谈
  - 2: 交易（未实现）
  - 3: 攻击（转为敌对并触发战斗）
```

## 性能优化

1. **碰撞检测**：使用平方距离比较，避免开方运算
2. **触发限制**：一次只处理一个遭遇，避免重复触发
3. **标记机制**：使用 `_encounter_triggered` 标记防止重复触发

## 未来扩展

1. **自动战斗**：在大地图上根据战斗力自动解决战斗
2. **谈判系统**：玩家可以选择与敌对NPC谈判，避免战斗
3. **逃跑系统**：玩家可以选择逃跑，有一定成功率
4. **多人战斗**：支持玩家队伍与敌人队伍的战斗
5. **战斗奖励**：战斗胜利后获得经验和战利品
6. **交易系统**：实现完整的交易界面和逻辑
7. **对话系统**：与中立NPC的对话可以触发任务或交易

## 文件变更清单

1. **修改文件**：
   - `entities/npc.py` - 添加 `faction` 属性
   - `game_gui.py` - 实现遭遇战系统

2. **新增文档**：
   - `docs/ENCOUNTER_SYSTEM.md` - 本文档

## 总结

遭遇战系统成功实现了大地图与战斗场景的无缝切换，为游戏增添了战略和战术两个层面的玩法。玩家现在可以：

- 在大地图上自由探索，遭遇不同的NPC军团
- 与敌对NPC自动触发战斗，体验激烈的战斗场景
- 与中立NPC交互，选择不同的互动方式

这个系统为后续的游戏内容扩展（如谈判、交易、任务等）提供了坚实的基础。


