# 新功能说明

本文档说明游戏新增的功能和改进。

## 新增功能

### 1. 交互式命令行界面 ✅

现在游戏有了完整的交互式命令行界面，玩家可以：

- 通过菜单系统导航
- 查看玩家状态
- 与NPC交互
- 管理任务
- 管理基地

**使用方法**: 运行 `python game.py` 启动完整游戏。

### 2. 任务系统 ✅

完整的任务系统，包括：

- **任务类型**:
  - 击败任务：击败指定数量的敌人
  - 收集任务：收集指定数量的物品
  - 交付任务（预留接口）
  - 护送任务（预留接口）
  - 探索任务（预留接口）
  - 建造任务（预留接口）

- **任务状态**:
  - 可接受
  - 进行中
  - 已完成
  - 失败（超时）

- **任务管理**:
  - 查看可用任务
  - 接受任务
  - 跟踪任务进度
  - 完成任务获得奖励

**示例**:
```python
# 创建任务
kill_quest = quest_manager.create_kill_quest(
    quest_id="quest_001",
    title="清理盗贼",
    description="击败3个盗贼",
    giver=npc,
    kill_count=3,
    reward_gold=200,
    reward_exp=100
)
```

### 3. 随机事件系统 ✅

随机事件系统为游戏增加了动态性和趣味性：

- **事件类型**:
  - 好天气：增加资源产量
  - 坏天气：减少资源产量
  - 商人到达：可以交易
  - 盗贼袭击：需要战斗
  - 意外收获：获得资源
  - 发现：探索相关事件

- **事件特性**:
  - 瞬时事件：立即生效
  - 持续事件：在一定时间内生效
  - 事件效果：影响资源、生产等
  - 事件选项：玩家可以选择应对方式

**事件触发**: 系统会定期检查并随机触发事件。

### 4. 改进的游戏循环 ✅

新的游戏循环支持：

- 实时更新系统
- 玩家交互
- 状态管理
- 平滑的游戏体验

## 使用新功能

### 运行完整游戏

```bash
python game.py
```

### 游戏内操作

1. **主菜单**: 选择要进行的活动
2. **探索**: 在世界中探索，可能发现资源或触发事件
3. **对话**: 与NPC对话，可以：
   - 打招呼
   - 询问任务
   - 自由对话（如果启用OpenAI）
   - 交易（即将推出）
4. **任务**: 查看和管理任务
5. **基地**: 管理资源和建筑

### 任务示例

游戏开始时会有一些预设任务：

1. **清理盗贼**: 击败3个敌人，获得200金币和100经验
2. **收集木材**: 收集10单位木材，获得150金币和80经验

### 事件示例

游戏会随机触发事件，例如：

- **好天气**: 资源产量增加50%，持续5分钟
- **意外收获**: 立即获得随机资源
- **商人到达**: 商人出现，可以交易（持续10分钟）

## 系统整合

所有系统都已整合到 `game.py` 中：

- 游戏引擎自动更新
- NPC AI系统运行
- 生产系统工作
- 任务系统跟踪进度
- 事件系统随机触发

## 未来改进

计划中的改进：

- [ ] 完整的交易系统
- [ ] 战斗界面
- [ ] 存档系统
- [ ] 更多任务类型
- [ ] 更多事件类型
- [ ] 图形界面（可选）

## 代码示例

### 创建自定义任务

```python
from systems.quest import QuestManager, QuestType

quest_manager = QuestManager()

# 创建一个收集任务
quest = quest_manager.create_collect_quest(
    quest_id="my_quest",
    title="收集矿石",
    description="收集20单位金属矿石",
    giver=merchant_npc,
    item_type="metal",
    count=20,
    reward_gold=300,
    reward_exp=150
)

quest_manager.add_quest(quest)
```

### 创建自定义事件

```python
from systems.event import EventManager, EventType, GameEvent

event_manager = EventManager()

# 创建一个自定义事件
event = GameEvent(
    event_id="custom_event_001",
    event_type=EventType.DISCOVERY,
    title="发现宝藏",
    description="你发现了一个隐藏的宝藏！",
    duration=0.0  # 瞬时事件
)

event_manager.add_event(event)
```

## 注意事项

1. **OpenAI集成**: 对话功能可以在 `config.json` 中启用OpenAI集成来增强
2. **保存游戏**: 存档功能正在开发中
3. **性能**: 大量NPC和事件可能会影响性能，建议适度使用

享受游戏！


