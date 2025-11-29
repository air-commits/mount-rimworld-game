# 项目目录结构解析

## 项目根目录

```
mount_rimworld_game/
├── game_gui_optimized.py      # 【主入口】优化版游戏主控制器
├── assets_library.py           # 【素材库】管理所有游戏素材资源
├── config.json                 # 游戏配置文件
├── requirements.txt            # Python依赖包列表
├── README.md                   # 项目说明文档
├── README_NEW.md               # 新版本说明文档
└── game_state.json             # 游戏状态保存文件（自动生成）
```

## 功能界面（独立main文件）

```
├── settings_main.py            # 设置界面主程序
├── inventory_main.py          # 背包界面主程序
├── army_main.py                # 军队界面主程序
├── nation_main.py              # 国家界面主程序
├── relations_main.py           # 关系界面主程序
└── minimap_main.py            # 小地图界面主程序
```

## 核心系统目录

### core/ - 核心游戏系统
```
core/
├── __init__.py                 # 模块初始化
├── world.py                    # 世界系统（地图、地形、位置）
├── game_engine.py              # 游戏引擎（核心循环、实体管理）
├── game_state.py               # 游戏状态管理
└── locations.py                # 地点系统（城镇、村庄等）
```

**功能说明：**
- `world.py`: 定义世界地图、地形类型、位置坐标系统
- `game_engine.py`: 游戏主循环、实体更新、系统管理
- `game_state.py`: 游戏状态保存和加载
- `locations.py`: 地点类型、地点生成、地点管理

### entities/ - 实体系统
```
entities/
├── __init__.py                 # 模块初始化
├── character.py                # 角色基类（所有角色的基础）
├── player.py                   # 玩家角色类
└── npc.py                      # NPC角色类
```

**功能说明：**
- `character.py`: 定义所有角色的基础属性和方法
- `player.py`: 玩家特有的属性和方法（金币、声望等）
- `npc.py`: NPC特有的属性和方法（性格、关系等）

### ui/ - 用户界面系统
```
ui/
├── __init__.py                 # 模块初始化
└── game_window.py              # 游戏窗口（Pygame图形界面）
```

**功能说明：**
- `game_window.py`: 负责所有图形渲染、窗口管理、UI绘制

### utils/ - 工具系统
```
utils/
├── __init__.py                 # 模块初始化
├── logger.py                   # 日志系统
└── config.py                   # 配置管理
```

**功能说明：**
- `logger.py`: 统一的日志记录系统
- `config.py`: 配置文件读取和管理

## 扩展系统目录

### ai/ - AI系统
```
ai/
├── __init__.py                 # 模块初始化
├── npc_ai.py                   # NPC AI逻辑
└── openai_integration.py       # OpenAI集成（可选）
```

**功能说明：**
- `npc_ai.py`: NPC的行为AI、决策逻辑
- `openai_integration.py`: OpenAI API集成（用于NPC对话）

### combat/ - 战斗系统
```
combat/
├── __init__.py                 # 模块初始化
├── combat_engine.py            # 战斗引擎
├── weapons.py                  # 武器系统
└── skills.py                   # 技能系统
```

**功能说明：**
- `combat_engine.py`: 战斗计算、伤害计算
- `weapons.py`: 武器定义、武器属性
- `skills.py`: 技能定义、技能效果

### colony/ - 基地系统
```
colony/
├── __init__.py                 # 模块初始化
├── resource.py                 # 资源管理
├── building.py                 # 建筑系统
└── production.py               # 生产系统
```

**功能说明：**
- `resource.py`: 资源类型、资源管理
- `building.py`: 建筑类型、建筑管理
- `production.py`: 生产链、生产效率

### systems/ - 游戏系统
```
systems/
├── __init__.py                 # 模块初始化
├── quest.py                    # 任务系统
└── event.py                    # 事件系统
```

**功能说明：**
- `quest.py`: 任务创建、任务管理、任务完成
- `event.py`: 随机事件、事件触发

## 其他目录

### logs/ - 日志文件
```
logs/
└── game_YYYYMMDD_HHMMSS.log    # 游戏运行日志（自动生成）
```

### docs/ - 文档目录
```
docs/
└── PROJECT_STRUCTURE.md        # 项目结构文档（本文件）
```

## 文件说明

### 主入口文件
- **game_gui_optimized.py**: 游戏主控制器，负责：
  - 初始化游戏世界（20x20地图）
  - 生成玩家、NPC、城镇、村庄
  - 处理玩家移动和输入
  - 管理界面切换
  - 保存/恢复游戏状态

### 素材库文件
- **assets_library.py**: 素材资源管理，负责：
  - 存储地图素材路径
  - 存储NPC素材路径
  - 存储角色素材路径
  - 存储地点素材路径
  - 提供素材获取接口

### 功能界面文件
所有 `*_main.py` 文件都是独立的界面模块：
- 接收游戏状态数据
- 显示对应功能界面
- 返回更新后的游戏状态
- 支持中文显示

## 数据流向

```
game_gui_optimized.py (主控制器)
    ↓ save_state()
功能界面 (settings_main.py 等)
    ↓ 修改数据
    ↓ 返回状态
game_gui_optimized.py
    ↓ restore_state()
继续游戏
```

## 依赖关系

```
game_gui_optimized.py
├── core.game_engine
├── core.world
├── entities.player
├── entities.npc
├── core.locations
├── ui.game_window
├── assets_library
└── utils.logger

功能界面 (*_main.py)
├── utils.logger
└── pygame

ui/game_window.py
├── core.world
├── entities.player
├── entities.npc
├── core.locations
└── utils.logger
```

## 修改建议

### 添加新功能界面
1. 创建新的 `*_main.py` 文件
2. 在 `game_gui_optimized.py` 的 `switch_to_interface()` 中添加切换逻辑
3. 在 `draw_bottom_buttons()` 中添加新按钮

### 添加素材
1. 在 `assets_library.py` 中添加素材路径
2. 在 `ui/game_window.py` 的 `draw_world_with_assets()` 中使用素材

### 修改地图
1. 修改 `core/world.py` 的地形生成逻辑
2. 修改 `game_gui_optimized.py` 的地图尺寸和生成逻辑

