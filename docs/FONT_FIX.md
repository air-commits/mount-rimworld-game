# 字体修复文档

## 问题描述

游戏运行时，所有中文文本（玩家名称、菜单选项等）都显示为"空心方块"（乱码）。

## 问题原因

`pygame.font.Font(None, size)` 使用的默认字体不支持中文字符，导致中文无法正确显示。

## 解决方案

修改 `ui/game_window.py` 中的字体初始化代码，优先使用系统自带的中文字体。

### 实现逻辑

1. **优先使用系统字体**:
   - 尝试加载常见的中文字体（simhei、microsoftyahei等）
   - 测试字体是否支持中文显示
   - 如果支持，使用该字体

2. **本地字体文件**:
   - 检测本地字体文件（如 `assets/font.ttf`）
   - 如果存在，优先使用

3. **保底方案**:
   - 如果都失败，使用默认字体（可能不支持中文，但不报错）

## 修复日志初始化顺序问题

### 问题

在 `GameWindow.__init__` 方法中，`self._load_font()` 被调用的位置太靠前了。`_load_font` 内部需要使用 `self.logger` 记录日志，但此时 `self.logger` 还没有被初始化（原本在 `__init__` 的最后才初始化），导致程序崩溃。

### 解决方案

将 `self.logger` 的初始化移到 `__init__` 方法的**第一行**，确保在调用 `_load_font()` 之前 logger 已经可用。

## 支持的中文字体列表

**Windows**:
- simhei (黑体)
- microsoftyahei (微软雅黑)
- simsun (宋体)
- kaiti (楷体)
- fangsong (仿宋)

**macOS**:
- STHeiti (黑体)
- PingFang SC (苹方)

**Linux**:
- WenQuanYi Micro Hei (文泉驿微米黑)
- Noto Sans CJK SC (Noto字体)

## 代码实现

### 修改后的 `__init__` 方法

```python
def __init__(self, width: int = 1024, height: int = 768):
    # === 🔴 修复：将 Logger 初始化移到第一行 ===
    # 必须先初始化 logger，因为后面的 _load_font 需要用到它
    self.logger = get_logger("GameWindow")
    
    pygame.init()
    # ... 其他初始化代码 ...
    
    # 字体初始化（现在调用 _load_font 是安全的）
    self.font_small = self._load_font(24)
    self.font_medium = self._load_font(32)
    self.font_large = self._load_font(48)
    # ... 其他代码 ...
```

### `_load_font()` 方法

```python
def _load_font(self, size: int):
    """加载字体（支持中文显示）"""
    # 1. 优先尝试使用系统自带的中文字体
    chinese_fonts = ['simhei', 'microsoftyahei', 'simsun', ...]
    
    for font_name in chinese_fonts:
        try:
            font = pygame.font.SysFont(font_name, size)
            # 测试字体是否支持中文
            test_surface = font.render('中', True, (255, 255, 255))
            if test_surface.get_width() > 0:
                self.logger.debug(f"成功加载中文字体: {font_name}")
                return font
        except:
            continue
    
    # 2. 尝试加载本地字体文件
    # ...
    
    # 3. 保底方案
    return pygame.font.Font(None, size)
```

## 使用方法

### 自动检测

游戏启动时会自动检测并加载合适的中文字体，无需手动配置。

### 添加自定义字体

如果需要使用自定义字体文件：

1. 将字体文件放在 `assets/font.ttf` 或 `assets/fonts/` 目录下
2. 游戏会自动检测并使用

## 测试

运行游戏后，检查：
- ✅ 玩家名称正确显示中文
- ✅ 菜单选项正确显示中文
- ✅ 所有UI文本正确显示中文
- ✅ 不再出现"空心方块"乱码
- ✅ 不再出现 AttributeError 错误

## 故障排除

### 如果仍然显示乱码

1. **检查系统字体**:
   - Windows: 打开"字体"设置，确认系统已安装中文字体
   - Linux: 安装中文字体包（如 `sudo apt-get install fonts-wqy-microhei`）

2. **使用自定义字体**:
   - 下载中文字体文件（如 simhei.ttf）
   - 放在 `assets/font.ttf` 位置
   - 重启游戏

3. **查看日志**:
   - 检查日志文件，查看字体加载情况
   - 确认是否成功加载了中文字体

## 技术细节

### 字体测试

使用 `font.render('中', True, (255, 255, 255))` 测试字体是否支持中文：
- 如果渲染成功（宽度 > 0），说明字体支持中文
- 如果不支持，继续尝试下一个字体

### 性能影响

字体加载只在初始化时执行一次，对游戏性能无影响。

### 跨平台兼容性

代码会自动适配不同操作系统：
- Windows: 使用 simhei、microsoftyahei 等
- macOS: 使用 STHeiti、PingFang SC 等
- Linux: 使用 WenQuanYi、Noto 等

## 修复的问题

1. ✅ **中文乱码问题**: 使用系统字体或自定义字体
2. ✅ **AttributeError 错误**: 将 logger 初始化移到最前面

## 总结

修复后，游戏应该能够：
- ✅ 正确显示所有中文文本
- ✅ 不再出现乱码问题
- ✅ 不再出现初始化错误

如果仍有问题，请检查系统是否安装了中文字体，或使用自定义字体文件。
