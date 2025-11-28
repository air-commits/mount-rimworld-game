# 大地图系统实现文档

## 概述

本系统实现了类似《骑马与砍杀》的大地图模式，与《环世界》风格的局部地图相结合。游戏现在支持两种场景模式：

1. **大地图模式 (World Map)**：玩家控制一个圆点（代表军团）在地图上移动，可以看到城镇、村庄、资源点等地标，以及其他NPC军团。
2. **局部地图模式 (Local Map)**：进入村庄、城镇等地点后，切换到此模式，可以看到详细的环世界风格地图，控制具体的士兵和建筑。

## 架构设计

### 核心组件

#### 1. 地点系统 (`core/locations.py`)

定义了大地图上的各种地点：

- **LocationType 枚举**：
  - `TOWN`: 城镇
  - `VILLAGE`: 村庄
  - `RESOURCE_POINT`: 资源点
  - `DUNGEON`: 地牢
  - `FORTRESS`: 要塞
  - `MARKET`: 市场

- **Location 类**：
  - 属性：名称、位置、类型、所属势力、人口、繁荣度等
  - 方法：`enter()` - 进入地点，`generate_local_map()` - 生成局部地图

- **LocationManager 类**：
  - 管理所有地点
  - 提供地点查询功能（按位置、按类型等）

#### 2. 军团系统 (`entities/player.py`)

玩家现在代表一支队伍（Party）：

- `party: List[Character]` - 队伍成员列表
- `add_member(character)` - 添加队员
- `remove_member(character)` - 移除队员
- `get_total_strength()` - 计算队伍总战斗力（用于大地图战斗预判）
- `get_party_size()` - 获取队伍大小

#### 3. 场景切换系统 (`game_gui.py`)

- `current_scene`: `'world_map'` 或 `'local_map'`
- `current_location`: 当前所在的地点（局部地图模式）
- `location_manager`: 地点管理器

**关键方法**：
- `enter_location(location)` - 进入地点，切换到局部地图
- `exit_location()` - 离开地点，返回大地图

### 渲染系统

#### 大地图渲染 (`ui/game_window.py`)

`draw_world_map()` 方法绘制大地图：

1. **背景**：简单的网格背景
2. **地点图标**：
   - 城镇：黄色圆点 + "城"标识
   - 村庄：绿色圆点 + "村"标识
   - 资源点：棕色圆点 + "资"标识
   - 地牢：红色圆点 + "牢"标识
3. **玩家军团**：蓝色圆点，显示名称和队伍大小
4. **NPC军团**：绿色圆点，显示名称

#### 局部地图渲染

使用现有的 `draw_world()` 方法，绘制详细的环世界风格地图。

## 交互控制

### 按键说明

- **WASD / 方向键**：移动
  - 大地图模式下：移动速度是局部地图的3倍
- **F键**：在大地图模式下，如果靠近地点（100像素内），按F进入地点
- **TAB键**：
  - 在大地图模式下：如果靠近地点，进入地点
  - 在局部地图模式下：返回大地图

### 场景切换逻辑

1. **进入地点**：
   - 检查玩家位置是否在地点附近（半径100像素）
   - 调用 `location.enter()` 生成或获取局部地图
   - 切换到 `local_map` 场景
   - 设置相机位置到局部地图中心

2. **离开地点**：
   - 切换回 `world_map` 场景
   - 恢复相机跟随玩家

## 使用示例

### 创建地点

```python
from core.locations import Location, LocationType
from core.world import Position

# 创建一个城镇
town = Location(
    name="铁炉堡",
    position=Position(800, 500),
    location_type=LocationType.TOWN,
    faction="alliance",
    population=500
)

# 添加到管理器
location_manager.add_location(town)
```

### 使用军团系统

```python
from entities.player import Player
from entities.npc import NPC

# 创建玩家（自动加入队伍）
player = Player(name="玩家")

# 添加NPC到队伍
npc = NPC(name="队友")
player.add_member(npc)

# 查看队伍信息
print(f"队伍大小: {player.get_party_size()}")
print(f"队伍战斗力: {player.get_total_strength()}")
```

## 未来扩展

1. **地点内容生成**：
   - 完善 `generate_local_map()` 方法，根据地点类型生成不同的建筑和NPC
   - 村庄：生成房屋、田地、村民
   - 城镇：生成更多建筑、商店、守卫
   - 地牢：生成敌人和宝箱

2. **大地图战斗**：
   - 实现军团之间的自动战斗
   - 使用 `get_total_strength()` 进行战斗预判

3. **时间系统**：
   - 大地图模式下时间流逝更快（按小时/天）
   - 局部地图模式下时间正常（按秒）

4. **资源点采集**：
   - 在资源点生成采集界面
   - 根据资源类型生成不同的采集逻辑

5. **商队系统**：
   - NPC可以组成商队在大地图上移动
   - 玩家可以攻击商队或与之交易

## 技术细节

### 性能优化

- 大地图模式下，NPC和地点使用简单的图标渲染，性能开销低
- 局部地图模式只在进入地点时加载，不占用额外内存

### 坐标系统

- 大地图和局部地图使用相同的 `Position` 坐标系统
- 相机系统自动处理坐标转换

## 文件变更清单

1. **新增文件**：
   - `core/locations.py` - 地点系统
   - `docs/WORLD_MAP_SYSTEM.md` - 本文档

2. **修改文件**：
   - `entities/player.py` - 添加军团系统
   - `game_gui.py` - 添加场景切换逻辑
   - `ui/game_window.py` - 添加大地图渲染方法
   - `core/__init__.py` - 导出Location相关类

## 总结

本系统成功实现了"大地图跑团 + 小地图战斗"的游戏架构，为游戏增添了战略层面的玩法。玩家现在可以：

- 在大地图上自由移动，探索不同的地点
- 进入地点后切换到详细的局部地图进行具体操作
- 管理自己的军团，与NPC军团互动

这个架构为后续的游戏内容扩展（如战斗、贸易、建设等）提供了坚实的基础。


