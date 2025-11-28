# OpenAI集成设置指南

本文档介绍如何配置和使用OpenAI集成功能来控制NPC的对话和行为。

## 前提条件

1. 本地部署OpenAI兼容API服务器
2. Python环境已安装requests库

## 本地部署OpenAI API

### 方式一：使用vLLM

vLLM是一个高性能的LLM推理和服务引擎，支持OpenAI兼容API。

```bash
# 安装vLLM
pip install vllm

# 启动服务（使用本地模型）
python -m vllm.entrypoints.openai.api_server \
    --model your-model-path \
    --port 8000
```

### 方式二：使用LocalAI

LocalAI是一个本地推理框架，支持多种模型。

```bash
# 下载LocalAI
git clone https://github.com/go-skynet/LocalAI.git
cd LocalAI

# 启动服务
docker-compose up -d
```

### 方式三：使用其他兼容服务

任何提供OpenAI兼容API的本地服务都可以使用，只需确保：
- 提供 `/v1/chat/completions` 端点
- 支持标准的OpenAI请求格式

## 配置游戏

编辑 `config.json` 文件：

```json
{
  "openai": {
    "enabled": true,
    "api_url": "http://localhost:8000/v1",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 150
  }
}
```

### 配置说明

- **enabled**: 是否启用OpenAI集成（true/false）
- **api_url**: OpenAI API的URL地址
- **model**: 使用的模型名称
- **temperature**: 生成文本的随机性（0.0-2.0），值越高越随机
- **max_tokens**: 生成文本的最大长度

## 使用示例

### 基本对话

```python
from ai.openai_integration import get_openai_integration
from entities.npc import NPC, NPCPersonality

# 创建NPC
npc = NPC(
    name="智能村民",
    position=Position(100, 100),
    personality=NPCPersonality(
        traits=["wise", "friendly"],
        kindness=80
    )
)

# 获取OpenAI集成
openai = get_openai_integration()

# 生成对话
response = openai.generate_npc_response(
    npc,
    "你好，最近发生了什么有趣的事情吗？"
)
print(f"{npc.name}: {response}")
```

### NPC行为决策

```python
# 生成NPC行为
situation = "玩家询问是否可以加入队伍"
options = ["同意", "拒绝", "提出条件"]

action = openai.generate_npc_action(npc, situation, options)
print(f"{npc.name} 决定: {action}")
```

## 对话上下文

系统会自动管理对话上下文，包括：
- NPC的个性特征
- 当前情绪和关系
- 对话历史（最近10条）
- 游戏上下文信息

## 提示词构建

系统会根据以下信息构建提示词：
1. NPC的基本信息（名称、个性）
2. 当前状态（情绪、关系）
3. 游戏上下文
4. 对话历史

提示词会自动格式化，确保OpenAI能够理解NPC的个性和状态。

## 故障排除

### 问题：无法连接OpenAI API

**解决方案**：
1. 检查API服务是否正在运行
2. 检查 `api_url` 配置是否正确
3. 检查网络连接和防火墙设置

### 问题：响应速度慢

**解决方案**：
1. 降低 `max_tokens` 值
2. 使用更小的模型
3. 检查API服务器的性能

### 问题：生成的内容不符合NPC个性

**解决方案**：
1. 调整 `temperature` 值（降低以增加一致性）
2. 检查NPC的个性设置是否合理
3. 调整提示词模板（修改 `openai_integration.py`）

## 高级配置

### 自定义提示词模板

编辑 `ai/openai_integration.py` 中的 `ConversationContext.to_prompt()` 方法来自定义提示词格式。

### 添加游戏上下文

在调用 `generate_npc_response()` 时传递 `game_context` 参数：

```python
game_context = {
    "current_time": "白天",
    "location": "村庄",
    "recent_events": ["风暴", "商队到达"]
}

response = openai.generate_npc_response(
    npc,
    "最近怎么样？",
    game_context=game_context
)
```

## 性能优化

1. **批量处理**: 可以批量生成多个NPC的响应（需要修改代码）
2. **缓存**: 对于相似的情况，可以考虑缓存响应
3. **异步调用**: 使用异步IO可以提高性能（需要修改代码）

## 安全注意事项

1. 确保API服务仅在本地网络可访问，或使用适当的身份验证
2. 不要将敏感信息传递给API
3. 定期检查生成的对话内容，避免不当内容

## 参考资源

- [OpenAI API文档](https://platform.openai.com/docs/api-reference)
- [vLLM文档](https://vllm.readthedocs.io/)
- [LocalAI文档](https://localai.io/)

