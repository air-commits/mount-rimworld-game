# 战斗冷却时间修复文档

## 问题描述

当前的 `CombatEngine.calculate_attack` 只是计算伤害，没有处理攻击间隔（Cooldown）。如果在游戏主循环中调用它，攻击者会每秒攻击 60 次（每帧攻击一次），导致攻击频率过快。

## 解决方案

添加 `process_combat_round()` 方法，在攻击前检查冷却时间，只有当冷却时间过了才允许攻击。

## 实现内容

### 1. 修改 CombatResult

添加 `attack_succeeded` 字段，用于表示是否成功发起攻击（冷却时间检查结果）。

### 2. 新增 process_combat_round() 方法

**方法签名**:
```python
def process_combat_round(
    self,
    attacker: Character,
    defender: Character,
    time_current: float,
    weapon: Optional[Weapon] = None,
    skill_manager: Optional[SkillManager] = None
) -> CombatResult
```

**功能**:
1. 检查攻击者是否有 `last_attack_time` 属性，如果没有则初始化为 0.0
2. 计算攻击速度（攻击间隔）：
   - 优先使用角色的 `attack_speed` 属性
   - 如果角色没有，但装备了武器，使用武器的 `attack_speed`
   - 如果都没有，根据敏捷计算（敏捷越高，攻击越快）
3. 检查冷却时间：只有当 `time_current - last_attack_time >= attack_speed` 时才允许攻击
4. 如果冷却时间未到，返回 `attack_succeeded=False` 的结果
5. 如果冷却时间已到，执行攻击并更新 `last_attack_time`

### 3. 新增 get_attack_cooldown_remaining() 方法

用于查询剩余冷却时间，可以用于显示冷却时间条。

## 攻击速度计算逻辑

### 默认攻击速度
- 默认：1.0 秒/次

### 武器攻击速度
- 如果武器有 `attack_speed` 属性（每秒攻击次数），转换为攻击间隔
- 例如：`attack_speed = 1.2`（每秒1.2次）→ 攻击间隔 = `1.0 / 1.2 ≈ 0.83秒`

### 徒手攻击速度
- 基础速度：1.0 秒/次
- 敏捷加成：敏捷越高，攻击越快
- 计算公式：`attack_speed = max(0.5, 1.0 - dexterity/100 * 0.3)`
- 最小攻击间隔：0.5秒（最快每秒2次）

## 使用示例

### 基础使用
```python
combat_engine = CombatEngine()
game_time = 10.5  # 当前游戏时间

# 处理战斗回合（会自动检查冷却时间）
result = combat_engine.process_combat_round(
    attacker=player,
    defender=enemy,
    time_current=game_time,
    weapon=player.equipped_weapon
)

if result.attack_succeeded:
    print(result)  # 显示攻击结果
    # 可以播放攻击动画
else:
    print("攻击冷却中...")
    # 不播放攻击动画
```

### 在游戏循环中使用
```python
def update_combat(delta_time, game_time):
    for attacker in combatants:
        target = attacker.target_entity
        if target and combat_engine.can_attack(attacker, target):
            result = combat_engine.process_combat_round(
                attacker=attacker,
                defender=target,
                time_current=game_time,
                weapon=attacker.equipped_weapon
            )
            
            if result.attack_succeeded:
                # 播放攻击动画
                play_attack_animation(attacker, target)
                # 显示伤害数字
                show_damage_number(result.damage_dealt)
```

### 查询冷却时间
```python
# 获取剩余冷却时间
remaining = combat_engine.get_attack_cooldown_remaining(
    attacker=player,
    time_current=game_time,
    weapon=player.equipped_weapon
)

if remaining > 0:
    print(f"攻击冷却中: {remaining:.2f}秒")
```

## 属性初始化

### 自动初始化

`process_combat_round()` 会自动为攻击者初始化 `last_attack_time` 属性（如果不存在）。

### 手动初始化（可选）

如果需要在角色创建时初始化：
```python
class Character:
    def __init__(self, ...):
        # ...
        self.last_attack_time = 0.0
        self.attack_speed = 1.0  # 可选：自定义攻击速度
```

## 攻击速度配置

### 武器攻击速度

武器定义中的 `attack_speed` 是每秒攻击次数：
```python
WEAPONS["iron_sword"] = Weapon(
    name="铁剑",
    attack_speed=1.2,  # 每秒1.2次 = 每0.83秒攻击一次
    ...
)
```

### 角色攻击速度

角色的 `attack_speed` 属性可以是：
- 攻击间隔（秒/次）：如 `1.0` 表示每秒攻击1次
- 或攻击频率（次/秒）：需要在代码中转换为间隔

当前实现中，如果角色有 `attack_speed` 属性，直接作为攻击间隔使用。

## 性能考虑

- 冷却时间检查非常简单（只比较时间差）
- 不会影响游戏性能
- 属性初始化只执行一次（首次攻击时）

## 向后兼容

- `calculate_attack()` 方法仍然保留，可以单独使用（不检查冷却）
- `process_combat_round()` 是新的推荐方法
- 现有代码使用 `calculate_attack()` 不会受影响

## 测试建议

### 测试攻击间隔
1. 创建两个角色，让一个攻击另一个
2. 观察攻击频率是否符合预期（默认约每秒1次）
3. 装备不同武器，测试武器攻击速度是否生效

### 测试冷却时间
1. 连续按键攻击，应该受冷却时间限制
2. 不同武器的攻击速度应该不同
3. 敏捷高的角色应该攻击更快

## 总结

通过添加 `process_combat_round()` 方法，解决了攻击频率过快的问题：

- ✅ 攻击速度可控（默认1秒/次）
- ✅ 武器影响攻击速度
- ✅ 敏捷影响徒手攻击速度
- ✅ 返回攻击是否成功的信息（用于播放动画）
- ✅ 性能优化（简单的时间比较）

现在战斗系统更加平衡和可控了！


