# -*- coding: utf-8 -*-
"""
VersaChat 上下文管理器
负责智能上下文构建、Token 估算、对话摘要、角色记忆管理
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import time


@dataclass
class ContextConfig:
    """上下文配置"""
    # 不同模型的上下文限制（tokens）
    MODEL_CONTEXT_LIMITS = {
        # 阿里 DashScope
        "qwen-max": 30000,
        "qwen-plus": 30000,
        "qwen-turbo": 6000,
        "qwen-long": 1000000,
        "qwen2.5-72b": 32000,
        "qwen2.5-32b": 32000,
        "qwen2.5-14b": 32000,
        "qwen2.5-7b": 32000,
        # OpenAI
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "gpt-4-turbo": 128000,
        "gpt-4": 8000,
        "gpt-3.5-turbo": 16000,
        "o1-preview": 128000,
        "o1-mini": 128000,
        # Anthropic
        "claude-3-5-sonnet": 200000,
        "claude-3-5-haiku": 200000,
        "claude-3-opus": 200000,
        "claude-3-sonnet": 200000,
        # Ollama 本地模型（保守估计）
        "llama": 8000,
        "mistral": 8000,
        "qwen": 32000,
        "deepseek": 32000,
        # 默认
        "default": 8000
    }
    
    # 上下文使用比例：预留空间给回复
    context_usage_ratio: float = 0.75
    
    # 系统提示词预留 token 数
    system_prompt_reserve: int = 2000
    
    # 启用摘要的对话轮数阈值
    summary_threshold: int = 15
    
    # 最小保留的最近消息数
    min_recent_messages: int = 5


class TokenEstimator:
    """Token 估算器"""
    
    @staticmethod
    def estimate(text: str) -> int:
        """
        估算文本的 token 数量
        
        规则：
        - 中文：约 1.2-1.5 字符/token
        - 英文：约 4 字符/token
        - 混合估算：约 2 字符/token
        """
        if not text:
            return 0
        
        # 统计中英文比例
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        total_chars = len(text)
        
        if total_chars == 0:
            return 0
        
        chinese_ratio = chinese_chars / total_chars
        
        # 根据中英文比例计算
        # 中文多：约 1.3 字符/token
        # 英文多：约 4 字符/token
        chars_per_token = 1.3 * chinese_ratio + 4 * (1 - chinese_ratio)
        
        return max(1, int(text.__len__() / chars_per_token))
    
    @staticmethod
    def estimate_messages(messages: List[Dict]) -> int:
        """估算消息列表的 token 数"""
        total = 0
        for msg in messages:
            # 消息内容
            total += TokenEstimator.estimate(msg.get("content", ""))
            # 角色名等元数据开销
            total += 5
        return total


class ContextWindowManager:
    """智能上下文窗口管理器"""
    
    def __init__(self, config: ContextConfig = None):
        self.config = config or ContextConfig()
        self.estimator = TokenEstimator()
    
    def get_context_limit(self, model_name: str) -> int:
        """获取模型的有效上下文限制"""
        model_lower = model_name.lower()
        
        for key, limit in self.config.MODEL_CONTEXT_LIMITS.items():
            if key in model_lower:
                return int(limit * self.config.context_usage_ratio)
        
        return int(self.config.MODEL_CONTEXT_LIMITS["default"] * self.config.context_usage_ratio)
    
    def build_context(self,
                      chat_history: List[Dict],
                      model_name: str,
                      system_prompt_tokens: int = 0) -> Tuple[List[Dict], bool]:
        """
        智能构建上下文
        
        Args:
            chat_history: 完整对话历史
            model_name: 模型名称
            system_prompt_tokens: 系统提示词已占用的 token 数
        
        Returns:
            (截断后的历史, 是否被截断)
        """
        limit = self.get_context_limit(model_name)
        available_tokens = limit - system_prompt_tokens - self.config.system_prompt_reserve
        
        if available_tokens <= 0:
            # 系统提示词太长，仅返回最近几条
            return chat_history[-self.config.min_recent_messages:], True
        
        # 从后往前累积，直到达到限制
        selected = []
        current_tokens = 0
        truncated = False
        
        for msg in reversed(chat_history):
            msg_tokens = self.estimator.estimate(msg.get("content", "")) + 10  # 元数据开销
            
            if current_tokens + msg_tokens > available_tokens:
                truncated = True
                break
            
            selected.insert(0, msg)
            current_tokens += msg_tokens
        
        # 确保至少保留最近几条
        if len(selected) < self.config.min_recent_messages and len(chat_history) >= self.config.min_recent_messages:
            selected = chat_history[-self.config.min_recent_messages:]
            truncated = True
        
        return selected, truncated


class RoleMemoryManager:
    """角色记忆管理器"""
    
    def __init__(self, config: ContextConfig = None):
        self.config = config or ContextConfig()
    
    def build_enhanced_system_prompt(self,
                                      role: Dict,
                                      other_roles: List[Dict],
                                      chat_history: List[Dict],
                                      context_truncated: bool = False) -> str:
        """
        构建增强版系统提示词
        
        结构：
        1. 核心人设（始终保留）
        2. 场景与其他角色
        3. 对话摘要（长对话时）
        4. 行为约束
        """
        sections = []
        
        # 1. 核心人设
        sections.append(f"""## 你的身份
你是 **{role['name']}**。

{role['persona']}""")
        
        # 2. 场景与其他角色
        if other_roles:
            others_desc = []
            for r in other_roles:
                if r['name'] != role['name']:
                    # 提取人设的前100字作为简介
                    brief = r['persona'][:100] + "..." if len(r['persona']) > 100 else r['persona']
                    others_desc.append(f"- **{r['name']}**: {brief}")
            
            if others_desc:
                sections.append(f"""## 对话中的其他角色
{chr(10).join(others_desc)}""")
        
        # 3. 对话摘要（长对话或被截断时）
        if context_truncated or len(chat_history) > self.config.summary_threshold:
            summary = self._extract_key_points(chat_history)
            if summary:
                sections.append(f"""## 对话背景摘要
以下是之前对话的关键信息：
{summary}""")
        
        # 4. 行为约束
        sections.append("""## 回复要求
- 始终保持你的角色特点和说话风格
- 自然地回应对话，不要生硬
- 不要在回复开头写自己的名字
- 回复长度适中，保持对话节奏
- 可以对其他角色的观点表达认同或异议""")
        
        return "\n\n".join(sections)
    
    def _extract_key_points(self, chat_history: List[Dict]) -> str:
        """提取对话关键点"""
        key_points = []
        
        # 提取所有旁白（场景指导）
        narrator_msgs = [m for m in chat_history if m.get("role") == "narrator"]
        if narrator_msgs:
            # 取最近的3条旁白
            for msg in narrator_msgs[-3:]:
                content = msg.get("content", "")[:150]
                key_points.append(f"- [旁白] {content}")
        
        # 提取对话开头的几条消息（建立语境）
        early_msgs = [m for m in chat_history[:5] if m.get("role") != "narrator"]
        for msg in early_msgs[:2]:
            name = msg.get("name", "Unknown")
            content = msg.get("content", "")[:100]
            key_points.append(f"- [{name}] {content}...")
        
        return "\n".join(key_points) if key_points else ""


class ConversationFlowController:
    """对话流控制器"""
    
    def __init__(self):
        self.min_delay = 0.5          # 最小延迟（秒）
        self.max_delay = 10.0         # 最大延迟（秒）
        self.base_delay = 1.0         # 基础延迟
        self.current_delay = 1.0      # 当前延迟
        self.consecutive_errors = 0   # 连续错误计数
        self.last_call_time = 0       # 上次调用时间
    
    def get_delay(self) -> float:
        """获取下一次调用应等待的延迟"""
        return self.current_delay
    
    def wait(self):
        """执行等待"""
        time.sleep(self.current_delay)
    
    def on_success(self):
        """调用成功时的回调"""
        self.consecutive_errors = 0
        # 逐步降低延迟
        self.current_delay = max(self.min_delay, self.current_delay * 0.9)
        self.last_call_time = time.time()
    
    def on_error(self, is_rate_limit: bool = False):
        """调用失败时的回调"""
        self.consecutive_errors += 1
        
        if is_rate_limit:
            # 限流时大幅增加延迟
            self.current_delay = min(self.max_delay, self.current_delay * 2.5)
        else:
            # 一般错误时适度增加延迟
            self.current_delay = min(self.max_delay, self.current_delay * 1.5)
    
    def should_pause(self) -> bool:
        """是否应该暂停对话（连续错误过多）"""
        return self.consecutive_errors >= 3
    
    def reset(self):
        """重置状态"""
        self.current_delay = self.base_delay
        self.consecutive_errors = 0


@dataclass
class ConversationState:
    """对话状态快照"""
    turn_index: int = 0
    round_count: int = 0
    last_speaker: str = ""
    context_truncated: bool = False
    total_tokens_used: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "turn_index": self.turn_index,
            "round_count": self.round_count,
            "last_speaker": self.last_speaker,
            "context_truncated": self.context_truncated,
            "total_tokens_used": self.total_tokens_used
        }


# 全局单例
_context_manager: Optional[ContextWindowManager] = None
_memory_manager: Optional[RoleMemoryManager] = None
_flow_controller: Optional[ConversationFlowController] = None


def get_context_manager() -> ContextWindowManager:
    """获取上下文管理器单例"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextWindowManager()
    return _context_manager


def get_memory_manager() -> RoleMemoryManager:
    """获取记忆管理器单例"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = RoleMemoryManager()
    return _memory_manager


def get_flow_controller() -> ConversationFlowController:
    """获取流控制器单例"""
    global _flow_controller
    if _flow_controller is None:
        _flow_controller = ConversationFlowController()
    return _flow_controller
