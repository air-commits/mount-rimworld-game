# 游戏架构说明

本文档详细说明游戏的整体架构和设计思路。

## 整体架构

游戏采用模块化设计，各个系统相对独立，通过接口交互。

```
游戏引擎 (GameEngine)
    ├── 世界系统 (World)
    ├── 状态管理 (GameState)
    └── 实体管理
        ├── 玩家 (Player)
        ├── NPC (NPC)
        └── 其他实体
    ├── 战斗系统 (CombatEngine)
    ├── 基地系统
    │   ├── 资源管理 (ResourceManager)
    │   ├── 建筑系统 (BuildingManager)
    │   └── 生产系统 (ProductionSystem)
    └── AI系统
        ├── NPC基础AI (NPCAI)
        └── OpenAI集成 (OpenAIIntegration)
```

## 核心模块说明

### 1. 核心引擎模块 (core/)

**GameEngine (game_engine.py)**
- 游戏主循环
- 系统更新调度
- 实体管理

**World (world.py)**
- 世界地图管理
- 地形系统
- 位置验证

**GameState (game_state.py)**
- 游戏状态切换
- 状态数据管理

### 2. 实体模块 (entities/)

**Character (character.py)**
- 所有角色的基类
- 基础属性系统
- 生命值和伤害系统
- 移动系统

**Player (player.py)**
- 玩家特有功能
- 金币和声望系统
- 经验值和升级

**NPC (npc.py)**
- NPC特有功能
- 个性系统
- 需求系统（环世界风格）
- 情绪系统
- 关系系统
- 对话历史

### 3. 战斗模块 (combat/)

**CombatEngine (combat_engine.py)**
- 战斗逻辑计算
- 伤害计算
- 命中判定
- 暴击和格挡

**Weapon (weapons.py)**
- 武器定义
- 武器属性
- 耐久度系统

**Skill (skills.py)**
- 技能系统
- 技能等级和经验
- 技能效果计算

### 4. 基地模块 (colony/)

**ResourceManager (resource.py)**
- 资源存储和管理
- 资源增加和消耗
- 资源检查

**Building (building.py)**
- 建筑定义
- 建筑属性（生命值、等级等）
- 建筑功能（生产、存储等）
- 建筑升级和修理

**ProductionSystem (production.py)**
- 生产配方管理
- 生产队列
- 资源转换

### 5. AI模块 (ai/)

**NPCAI (npc_ai.py)**
- NPC基础行为决策
- AI状态机
- 需求驱动行为

**OpenAIIntegration (openai_integration.py)**
- OpenAI API集成
- 对话生成
- 行为决策
- 上下文管理

### 6. 工具模块 (utils/)

**Logger (logger.py)**
- 日志记录系统
- 控制台和文件输出

**Config (config.py)**
- 配置文件管理
- 配置读取和保存

## 数据流

### 游戏循环

```
开始
  ↓
初始化引擎和系统
  ↓
主循环开始
  ↓
[更新世界系统]
  ↓
[更新所有实体]
  ↓
[更新战斗系统]
  ↓
[更新基地系统]
  ↓
[更新AI系统]
  ↓
[渲染（如果有图形界面）]
  ↓
检查退出条件
  ↓
否 → 返回主循环开始
  ↓
是 → 结束
```

### 战斗流程

```
攻击者发起攻击
  ↓
检查攻击距离
  ↓
计算命中率
  ↓
[未命中] → 结束
  ↓
[命中]
  ↓
检查格挡
  ↓
[格挡成功] → 结束
  ↓
[格挡失败]
  ↓
计算基础伤害
  ↓
应用属性加成
  ↓
应用技能加成
  ↓
检查暴击
  ↓
应用伤害
  ↓
结束
```

### NPC决策流程

```
AI更新
  ↓
检查需求（食物、休息等）
  ↓
[需求不足] → 设置相应状态（寻找食物、休息等）
  ↓
[需求满足]
  ↓
检查当前状态
  ↓
执行状态对应的行为
  ↓
定期重新决策
```

## 设计模式

### 单例模式
- Logger: 全局日志实例
- Config: 全局配置实例
- OpenAIIntegration: 全局AI集成实例

### 组件模式
- Character及其子类：角色作为组件
- Building: 建筑作为组件

### 策略模式
- 不同武器类型有不同的伤害计算策略
- 不同AI状态有不同的行为策略

## 扩展点

### 添加新武器类型
1. 在 `combat/weapons.py` 的 `WeaponType` 枚举中添加新类型
2. 在 `WEAPONS` 字典中添加新武器定义

### 添加新建筑类型
1. 在 `colony/building.py` 的 `BuildingType` 枚举中添加新类型
2. 在 `BUILDING_COSTS` 字典中添加建筑成本

### 添加新资源类型
1. 在 `colony/resource.py` 的 `ResourceType` 枚举中添加新类型

### 添加新AI行为
1. 在 `ai/npc_ai.py` 的 `AIState` 枚举中添加新状态
2. 在 `execute_state()` 方法中添加状态处理逻辑

## 性能考虑

1. **实体更新**: 只更新活跃实体
2. **距离检查**: 使用空间分割优化（未来改进）
3. **AI决策**: 限制决策频率，避免过度计算
4. **OpenAI调用**: 异步调用，避免阻塞主循环（未来改进）

## 未来改进

1. **空间分割**: 使用四叉树等数据结构优化空间查询
2. **事件系统**: 解耦系统间的通信
3. **存档系统**: 实现游戏状态保存和加载
4. **任务系统**: 实现任务生成和执行
5. **图形界面**: 使用pygame或其他库添加可视化
6. **网络支持**: 多人游戏支持（可选）

## 代码风格

- 所有代码使用中文注释
- 函数和类都有详细的文档字符串
- 变量和函数名使用英文，注释使用中文
- 遵循PEP 8 Python代码规范

