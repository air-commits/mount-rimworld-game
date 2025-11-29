# 骑砍环世界融合游戏

## 📖 项目简介

这是一个基于 Pygame 开发的图形界面游戏，融合了《骑马与砍杀》和《环世界》的游戏元素。

## 🎮 游戏特性

- **20x20 地图系统**：简洁的地图设计，专注于游戏玩法
- **多界面系统**：设置、背包、军队、国家、关系等独立界面
- **状态保存/恢复**：支持游戏状态保存和恢复
- **素材库系统**：集中管理游戏资源
- **模块化设计**：代码结构清晰，易于扩展

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行游戏

```bash
python game_gui_optimized.py
```

## 🎯 操作说明

### 基本操作
- **WASD / 方向键**：移动玩家
- **ESC**：暂停/返回
- **鼠标点击**：点击底部按钮切换界面

### 界面切换
- **设置**：游戏设置界面
- **暂停/开始**：暂停或继续游戏
- **背包**：查看和管理物品
- **军队**：管理军队单位
- **国家**：管理国家资源
- **关系**：查看和管理NPC关系

## 📁 项目结构

```
mount_rimworld_game/
├── game_gui_optimized.py    # 游戏主控制器（启动入口）
├── base_main.py              # 界面基类
├── assets_library.py         # 素材库
├── settings_main.py          # 设置界面
├── inventory_main.py         # 背包界面
├── army_main.py              # 军队界面
├── nation_main.py            # 国家界面
├── relations_main.py         # 关系界面
├── minimap_main.py           # 小地图界面
├── core/                     # 核心游戏系统
├── entities/                 # 实体系统
├── ui/                       # 用户界面系统
├── utils/                    # 工具系统
└── docs/                     # 项目文档
```

## 📚 文档

- [项目结构说明](docs/PROJECT_STRUCTURE.md) - 详细的项目结构介绍
- [文件介绍](docs/FILES_INTRODUCTION.md) - 所有文件的详细说明

## 🛠️ 开发说明

### 添加新功能界面

1. 创建新的 `*_main.py` 文件
2. 继承 `BaseMain` 类
3. 重写 `draw()` 方法实现界面绘制
4. 在 `game_gui_optimized.py` 中添加切换逻辑

### 添加素材

1. 在 `assets_library.py` 中添加素材路径
2. 在 `ui/game_window.py` 中使用素材

## 📝 代码规范

- 所有代码都有详细的中文注释
- 遵循 PEP 8 代码风格
- 使用类型提示（Type Hints）
- 模块化设计，易于维护

## 📄 许可证

本项目仅供学习和研究使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**注意**：本项目仍在开发中，部分功能可能不完整。

