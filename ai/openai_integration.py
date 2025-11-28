"""
OpenAI集成模块
用于连接本地部署的OpenAI API，控制NPC的对话和行为
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import json

from utils.logger import get_logger
from utils.config import get_config
from entities.npc import NPC


@dataclass
class ConversationContext:
    """对话上下文"""
    npc_name: str                      # NPC名称
    npc_personality: Dict[str, Any]    # NPC个性信息
    npc_mood: str                      # NPC当前情绪
    relationship: str                  # 与玩家的关系
    conversation_history: List[Dict[str, str]] = field(default_factory=list)  # 对话历史
    game_context: Dict[str, Any] = field(default_factory=dict)  # 游戏上下文
    
    def to_prompt(self) -> str:
        """
        将上下文转换为OpenAI提示词
        
        Returns:
            提示词字符串
        """
        prompt = f"""你是一个名为 {self.npc_name} 的游戏NPC。

个性特征：
{json.dumps(self.npc_personality, ensure_ascii=False, indent=2)}

当前情绪：{self.npc_mood}
与玩家的关系：{self.relationship}

游戏上下文：
{json.dumps(self.game_context, ensure_ascii=False, indent=2)}

对话历史：
"""
        for conv in self.conversation_history[-5:]:  # 最近5条对话
            prompt += f"{conv.get('speaker', 'unknown')}: {conv.get('message', '')}\n"
        
        prompt += "\n请以这个NPC的身份回复玩家，回复要符合NPC的个性和当前状态。回复要简洁，不超过50字。"
        
        return prompt


class OpenAIIntegration:
    """OpenAI API集成类"""
    
    def __init__(self):
        """初始化OpenAI集成"""
        self.logger = get_logger("OpenAIIntegration")
        self.config = get_config()
        
        # 检查OpenAI是否启用
        self.enabled = self.config.get("openai.enabled", False)
        
        if self.enabled:
            self.api_url = self.config.get("openai.api_url", "http://localhost:8000/v1")
            self.model = self.config.get("openai.model", "gpt-3.5-turbo")
            self.temperature = self.config.get("openai.temperature", 0.7)
            self.max_tokens = self.config.get("openai.max_tokens", 150)
            
            # 检查API是否可用
            self._check_api_available()
        else:
            self.logger.info("OpenAI集成已禁用（在config.json中启用）")
    
    def _check_api_available(self):
        """检查OpenAI API是否可用"""
        try:
            import requests
            
            # 尝试连接API（检查健康状态）
            health_url = self.api_url.replace("/v1", "/health") if "/v1" in self.api_url else f"{self.api_url}/health"
            
            try:
                response = requests.get(health_url, timeout=2)
                if response.status_code == 200:
                    self.logger.info(f"OpenAI API连接成功: {self.api_url}")
                    return
            except:
                pass
            
            # 如果健康检查失败，尝试直接调用API
            self.logger.warning(f"OpenAI API健康检查失败，将在使用时测试连接")
            
        except ImportError:
            self.logger.warning("requests库未安装，OpenAI集成功能受限")
            self.enabled = False
    
    def generate_npc_response(
        self,
        npc: NPC,
        player_message: str,
        game_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        使用OpenAI生成NPC响应
        
        Args:
            npc: NPC对象
            player_message: 玩家消息
            game_context: 游戏上下文（可选）
            
        Returns:
            NPC响应文本
        """
        if not self.enabled:
            # 如果未启用，返回基础响应
            return self._generate_basic_response(npc, player_message)
        
        try:
            # 构建对话上下文
            context = ConversationContext(
                npc_name=npc.name,
                npc_personality={
                    "traits": npc.personality.traits,
                    "kindness": npc.personality.kindness,
                    "aggression": npc.personality.aggression,
                    "loyalty": npc.personality.loyalty,
                    "profession": npc.personality.profession
                },
                npc_mood=npc.mood.value,
                relationship=npc.relationship_with_player.value,
                conversation_history=npc.conversation_history,
                game_context=game_context or {}
            )
            
            # 调用OpenAI API
            response = self._call_openai_api(context, player_message)
            
            # 记录对话
            npc.add_conversation("player", player_message)
            npc.add_conversation(npc.name, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"生成NPC响应失败: {e}")
            # 失败时返回基础响应
            return self._generate_basic_response(npc, player_message)
    
    def _call_openai_api(self, context: ConversationContext, user_message: str) -> str:
        """
        调用OpenAI API
        
        Args:
            context: 对话上下文
            user_message: 用户消息
            
        Returns:
            API响应文本
        """
        try:
            import requests
            
            # 构建提示词
            system_prompt = context.to_prompt()
            
            # 构建API请求
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            # 发送请求
            response = requests.post(
                f"{self.api_url}/chat/completions",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return content.strip()
            else:
                self.logger.error(f"OpenAI API请求失败: {response.status_code} - {response.text}")
                return "（连接错误）"
                
        except ImportError:
            self.logger.error("requests库未安装，无法调用OpenAI API")
            return "（功能未启用）"
        except Exception as e:
            self.logger.error(f"调用OpenAI API时出错: {e}")
            return "（错误）"
    
    def generate_npc_action(
        self,
        npc: NPC,
        situation: str,
        options: List[str]
    ) -> Optional[str]:
        """
        使用OpenAI生成NPC行为决策
        
        Args:
            npc: NPC对象
            situation: 当前情况描述
            options: 可选行为列表
            
        Returns:
            选择的行为（如果成功）
        """
        if not self.enabled:
            return None
        
        try:
            import requests
            
            prompt = f"""NPC: {npc.name}
个性: {', '.join(npc.personality.traits)}
情绪: {npc.mood.value}
关系: {npc.relationship_with_player.value}

当前情况: {situation}

可选行为: {', '.join(options)}

请根据NPC的个性和当前状态，选择一个最合适的行为。只回复行为名称，不要其他内容。
"""
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是一个游戏AI助手，帮助NPC做决策。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,  # 行为决策使用较低温度
                "max_tokens": 50
            }
            
            response = requests.post(
                f"{self.api_url}/chat/completions",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                action = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                
                # 检查返回的行为是否在选项中
                for option in options:
                    if option.lower() in action.lower() or action.lower() in option.lower():
                        return option
                
                return options[0] if options else None
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"生成NPC行为失败: {e}")
            return None
    
    def _generate_basic_response(self, npc: NPC, player_message: str) -> str:
        """
        生成基础响应（OpenAI未启用时的备用方案）
        
        Args:
            npc: NPC对象
            player_message: 玩家消息
            
        Returns:
            基础响应文本
        """
        # 简单的关键词匹配响应
        message_lower = player_message.lower()
        
        if "你好" in player_message or "hello" in message_lower:
            if npc.personality.kindness > 70:
                return f"你好！很高兴见到你，我是{npc.name}。"
            elif npc.personality.aggression > 70:
                return f"有什么事？我是{npc.name}。"
            else:
                return f"你好，我是{npc.name}。"
        elif "任务" in player_message or "quest" in message_lower:
            return "我现在没有任务可以给你。"
        elif "帮助" in player_message or "help" in message_lower:
            return "如果需要帮助，可以问问其他人。"
        else:
            if npc.mood.value == "happy":
                return "今天心情不错！"
            elif npc.mood.value == "angry":
                return "我现在心情不太好。"
            else:
                return "嗯..."


# 全局OpenAI集成实例
_openai_integration = None

def get_openai_integration() -> OpenAIIntegration:
    """
    获取全局OpenAI集成实例（单例模式）
    
    Returns:
        OpenAIIntegration实例
    """
    global _openai_integration
    if _openai_integration is None:
        _openai_integration = OpenAIIntegration()
    return _openai_integration

