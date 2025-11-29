# 项目文件介绍

## 📁 项目结构

```
mount_rimworld_game/
├── 【主程序文件】
│   ├── game_gui_optimized.py    # 游戏主控制器（启动入口）
│   └── base_main.py              # 界面基类（所有界面的基础）
│
├── 【功能界面文件】
│   ├── settings_main.py          # 设置界面
│   ├── inventory_main.py         # 背包界面
│   ├── army_main.py              # 军队界面
│   ├── nation_main.py            # 国家界面
│   ├── relations_main.py         # 关系界面
│   └── minimap_main.py           # 小地图界面
│
├── 【核心系统】
│   ├── core/                     # 核心游戏系统
│   │   ├── world.py              # 世界系统（地图、地形）
│   │   ├── game_engine.py        # 游戏引擎（核心循环）
│   │   ├── game_state.py         # 游戏状态管理
│   │   └── locations.py          # 地点系统（城镇、村庄）
│   │
│   ├── entities/                 # 实体系统
│   │   ├── character.py          # 角色基类
│   │   ├── player.py             # 玩家角色
│   │   └── npc.py                # NPC角色
│   │
│   ├── ui/                       # 用户界面系统
│   │   └── game_window.py       # 游戏窗口（Pygame渲染）
│   │
│   └── utils/                    # 工具系统
│       ├── logger.py             # 日志系统
│       └── config.py             # 配置管理
│
├── 【扩展系统】
│   ├── ai/                       # AI系统
│   ├── combat/                   # 战斗系统
│   ├── colony/                   # 基地系统
│   └── systems/                  # 游戏系统（任务、事件）
│
├── 【资源管理】
│   └── assets_library.py         # 素材库（管理游戏资源）
│
├── 【配置文件】
│   ├── config.json               # 游戏配置
│   ├── requirements.txt          # Python依赖
│   └── game_state.json           # 游戏状态（自动生成）
│
└── 【文档】
    └── docs/                     # 项目文档
```

---

## 📄 主要文件详细介绍

### 🎮 主程序文件

#### `game_gui_optimized.py` - 游戏主控制器
**作用**：游戏的主入口和核心控制器

**主要功能**：
- 初始化游戏世界（20x20地图）
- 生成玩家、NPC、城镇、村庄
- 处理玩家移动和输入
- 管理界面切换（设置、背包、军队等）
- 保存/恢复游戏状态

**关键类**：
- `GameGUI`：游戏主控制器类

**关键方法**：
- `__init__()`：初始化游戏系统
- `initialize_world()`：初始化游戏世界
- `save_state()`：保存游戏状态
- `restore_state()`：恢复游戏状态
- `game_loop()`：游戏主循环
- `handle_keydown()`：处理键盘输入
- `handle_mouse_click()`：处理鼠标点击
- `draw()`：绘制游戏画面

**使用方式**：
```bash
python game_gui_optimized.py
```

---

#### `base_main.py` - 界面基类
**作用**：所有独立界面主程序的基类，提供通用功能

**主要功能**：
- 字体加载（支持中文显示）
- 事件处理（ESC退出等）
- 基本绘制（背景、标题、提示）
- 游戏循环管理

**关键类**：
- `BaseMain`：界面基类

**关键方法**：
- `__init__()`：初始化界面
- `_load_font()`：加载字体（支持中文）
- `handle_events()`：处理事件
- `draw()`：绘制界面（子类可重写）
- `run()`：运行界面主循环

**设计模式**：模板方法模式，子类只需继承并重写 `draw()` 方法即可

---

### 🎨 功能界面文件

#### `settings_main.py` - 设置界面
**作用**：游戏设置界面

**功能**：
- 显示设置选项
- 返回主地图

**继承**：`BaseMain`

---

#### `inventory_main.py` - 背包界面
**作用**：玩家背包管理界面

**功能**：
- 显示玩家物品
- 管理物品使用
- 返回主地图

**继承**：`BaseMain`

---

#### `army_main.py` - 军队界面
**作用**：军队管理界面

**功能**：
- 显示军队信息
- 管理军队单位
- 返回主地图

**继承**：`BaseMain`

---

#### `nation_main.py` - 国家界面
**作用**：国家管理界面

**功能**：
- 显示国家信息
- 管理国家资源
- 返回主地图

**继承**：`BaseMain`

---

#### `relations_main.py` - 关系界面
**作用**：关系管理界面

**功能**：
- 显示NPC关系
- 管理外交关系
- 返回主地图

**继承**：`BaseMain`

---

#### `minimap_main.py` - 小地图界面
**作用**：小地图显示界面

**功能**：
- 显示小地图
- 地图导航
- 返回主地图

**继承**：`BaseMain`（重写了 `draw()` 方法以显示地图）

---

### 🎯 核心系统文件

#### `core/world.py` - 世界系统
**作用**：管理游戏世界的地图和地形

**主要功能**：
- 创建世界地图
- 管理地形类型（草地、森林、山脉等）
- 位置坐标系统
- 碰撞检测

**关键类**：
- `World`：世界类
- `TerrainType`：地形类型枚举
- `Position`：位置坐标类

---

#### `core/game_engine.py` - 游戏引擎
**作用**：游戏的核心逻辑引擎

**主要功能**：
- 游戏主循环
- 实体管理（玩家、NPC等）
- 系统更新
- 事件处理

**关键类**：
- `GameEngine`：游戏引擎类

---

#### `core/locations.py` - 地点系统
**作用**：管理游戏中的地点（城镇、村庄等）

**主要功能**：
- 创建地点
- 管理地点类型
- 地点交互

**关键类**：
- `Location`：地点类
- `LocationType`：地点类型枚举

---

#### `entities/player.py` - 玩家角色
**作用**：玩家角色的定义和管理

**主要功能**：
- 玩家属性（生命值、金币等）
- 玩家移动
- 玩家交互

**关键类**：
- `Player`：玩家类（继承自 `Character`）

---

#### `entities/npc.py` - NPC角色
**作用**：NPC角色的定义和管理

**主要功能**：
- NPC属性
- NPC行为
- NPC交互

**关键类**：
- `NPC`：NPC类（继承自 `Character`）

---

#### `ui/game_window.py` - 游戏窗口
**作用**：Pygame图形窗口，负责所有图形渲染

**主要功能**：
- 窗口管理
- 图形渲染（地图、实体、UI）
- 事件处理
- 相机系统

**关键类**：
- `GameWindow`：游戏窗口类
- `GameView`：视图模式枚举

**关键方法**：
- `draw_world()`：绘制世界地图
- `draw_world_with_assets()`：使用素材绘制世界
- `draw_hud()`：绘制HUD（抬头显示）
- `draw_trade()`：绘制交易界面
- `draw_dialog()`：绘制对话界面

---

### 🛠️ 工具系统文件

#### `utils/logger.py` - 日志系统
**作用**：统一的日志记录系统

**主要功能**：
- 日志记录
- 日志级别管理
- 日志文件输出

**使用方式**：
```python
from utils.logger import get_logger
logger = get_logger("模块名")
logger.info("信息")
logger.error("错误")
```

---

#### `utils/config.py` - 配置管理
**作用**：管理游戏配置文件

**主要功能**：
- 读取配置文件
- 配置项管理
- 配置验证

---

### 📦 资源管理文件

#### `assets_library.py` - 素材库
**作用**：集中管理所有游戏素材资源

**主要功能**：
- 存储素材路径（地图、角色、NPC、地点）
- 提供素材获取接口
- 素材加载管理

**关键类**：
- `AssetsLibrary`：素材库类

**关键方法**：
- `add_map_asset()`：添加地图素材
- `get_map_asset()`：获取地图素材
- `add_npc_asset()`：添加NPC素材
- `get_npc_asset()`：获取NPC素材
- `add_character_asset()`：添加角色素材
- `get_character_asset()`：获取角色素材
- `add_location_asset()`：添加地点素材
- `get_location_asset()`：获取地点素材

---

## 🔄 数据流向

```
启动游戏
  ↓
game_gui_optimized.py (主控制器)
  ↓
初始化世界（20x20地图）
  ↓
生成玩家、NPC、城镇、村庄
  ↓
游戏循环
  ├── 玩家移动
  ├── 绘制地图
  ├── 绘制HUD
  └── 绘制底部按钮
  ↓
点击按钮 → 保存状态 → 切换到功能界面 → 返回状态 → 恢复状态
```

---

## 📝 文件依赖关系

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
├── base_main
└── utils.logger

ui/game_window.py
├── core.world
├── entities.player
├── entities.npc
├── core.locations
└── utils.logger
```

---

## 🎯 使用建议

### 添加新功能界面
1. 创建新的 `*_main.py` 文件
2. 继承 `BaseMain` 类
3. 重写 `draw()` 方法实现界面绘制
4. 在 `game_gui_optimized.py` 中添加切换逻辑

### 添加素材
1. 在 `assets_library.py` 中添加素材路径
2. 在 `ui/game_window.py` 中使用素材

### 修改地图
1. 修改 `core/world.py` 的地形生成逻辑
2. 修改 `game_gui_optimized.py` 的地图尺寸

---

## 📚 相关文档

- `docs/PROJECT_STRUCTURE.md` - 项目结构详细说明
- `README.md` - 项目说明文档

