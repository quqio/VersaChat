# -*- coding: utf-8 -*-
"""
VersaChat LLM 后端
支持多平台 API：DashScope、OpenAI、Anthropic Claude、Ollama
"""

import requests
import time
from functools import wraps
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Callable
from http import HTTPStatus

# 尝试导入各平台 SDK
try:
    import dashscope
    HAS_DASHSCOPE = True
except ImportError:
    HAS_DASHSCOPE = False
    print("[Warning] dashscope 未安装，DashScope 模型将不可用")

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("[Warning] anthropic 未安装，Claude 模型将不可用")

from config_manager import get_config_manager


# ================== 重试装饰器 ==================
def with_retry(max_retries: int = 3, 
               base_delay: float = 1.0, 
               backoff: float = 2.0,
               retryable_exceptions: tuple = (Exception,)):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟（秒）
        backoff: 退避系数
        retryable_exceptions: 可重试的异常类型
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_error = e
                    error_msg = str(e).lower()
                    
                    # 检测限流错误
                    is_rate_limit = any(kw in error_msg for kw in 
                                        ["rate limit", "too many requests", "429", "quota"])
                    
                    if attempt < max_retries - 1:
                        delay = base_delay * (backoff ** attempt)
                        if is_rate_limit:
                            delay *= 2  # 限流时额外加倍等待
                        print(f"[Retry] 第 {attempt + 1} 次重试，等待 {delay:.1f}s: {e}")
                        time.sleep(delay)
                    else:
                        print(f"[Retry] 已达到最大重试次数 ({max_retries})")
            
            raise last_error
        return wrapper
    return decorator


class BaseLLMInterface(ABC):
    """LLM 接口基类"""
    
    def __init__(self, model_name: str, api_key: str = "", base_url: str = ""):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self._current_role_name = ""  # 当前角色名（用于消息格式化）
    
    def set_current_role(self, role_name: str):
        """设置当前角色名（用于区分自己和他人的消息）"""
        self._current_role_name = role_name
    
    @abstractmethod
    def chat(self, system_prompt: str, history_messages: List[Dict]) -> str:
        """
        发送对话请求
        
        Args:
            system_prompt: 系统提示词
            history_messages: 对话历史 [{"role": "user/assistant/narrator", "content": "...", "name": "..."}]
        
        Returns:
            模型回复内容
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """测试连接是否正常"""
        pass
    
    def _format_history_for_chat(self, system_prompt: str, 
                                  history_messages: List[Dict],
                                  current_role_name: str = "") -> List[Dict]:
        """
        将群聊历史格式化为标准对话格式（增强版）
        
        格式策略：
        - 系统提示词 → system 角色
        - 旁白消息 → user 角色，带 [旁白] 标记
        - 当前角色之前的发言 → assistant 角色
        - 其他角色的发言 → user 角色，带角色名标记
        """
        role_name = current_role_name or self._current_role_name
        formatted_msgs = [{'role': 'system', 'content': system_prompt}]
        
        for msg in history_messages:
            msg_role = msg.get('role', '')
            name = msg.get('name', 'Unknown')
            content = msg.get('content', '')
            
            if msg_role == 'narrator':
                # 旁白作为场景指导
                formatted_msgs.append({
                    'role': 'user', 
                    'content': f"[旁白/场景]: {content}"
                })
            elif name == role_name:
                # 自己之前的发言 → assistant
                formatted_msgs.append({
                    'role': 'assistant', 
                    'content': content
                })
            else:
                # 其他角色的发言 → user
                formatted_msgs.append({
                    'role': 'user', 
                    'content': f"[{name}]: {content}"
                })
        
        return formatted_msgs


class DashScopeInterface(BaseLLMInterface):
    """阿里 DashScope 接口"""
    
    def __init__(self, model_name: str, api_key: str = ""):
        config = get_config_manager()
        super().__init__(
            model_name=model_name,
            api_key=api_key or config.get_dashscope_key()
        )
    
    @with_retry(max_retries=3, base_delay=1.0, backoff=2.0)
    def chat(self, system_prompt: str, history_messages: List[Dict]) -> str:
        if not HAS_DASHSCOPE:
            raise RuntimeError("dashscope 库未安装")
        
        dashscope.api_key = self.api_key
        formatted_msgs = self._format_history_for_chat(system_prompt, history_messages)
        
        response = dashscope.Generation.call(
            model=self.model_name,
            messages=formatted_msgs,
            result_format='message',
        )
        if response.status_code == HTTPStatus.OK:
            return response.output.choices[0].message.content
        else:
            raise Exception(f"DashScope Error: {response.code} - {response.message}")
    
    def test_connection(self) -> tuple[bool, str]:
        if not HAS_DASHSCOPE:
            return False, "dashscope 库未安装"
        if not self.api_key:
            return False, "API Key 未配置"
        
        try:
            dashscope.api_key = self.api_key
            response = dashscope.Generation.call(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hi"}],
                result_format='message',
            )
            if response.status_code == HTTPStatus.OK:
                return True, "连接成功"
            else:
                return False, f"错误: {response.code}"
        except Exception as e:
            return False, str(e)


class OpenAIInterface(BaseLLMInterface):
    """OpenAI 兼容接口（支持 OpenAI 及兼容服务）"""
    
    def __init__(self, model_name: str, api_key: str = "", base_url: str = ""):
        config = get_config_manager()
        super().__init__(
            model_name=model_name,
            api_key=api_key or config.get_openai_key(),
            base_url=base_url or config.get_openai_base_url()
        )
    
    @with_retry(max_retries=3, base_delay=1.0, backoff=2.0)
    def chat(self, system_prompt: str, history_messages: List[Dict]) -> str:
        formatted_msgs = self._format_history_for_chat(system_prompt, history_messages)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": formatted_msgs,
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            error_msg = response.json().get('error', {}).get('message', response.text)
            raise Exception(f"OpenAI Error ({response.status_code}): {error_msg}")
    
    def test_connection(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, "API Key 未配置"
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            url = f"{self.base_url.rstrip('/')}/models"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True, "连接成功"
            else:
                return False, f"错误: {response.status_code}"
        except Exception as e:
            return False, str(e)


class AnthropicInterface(BaseLLMInterface):
    """Anthropic Claude 接口"""
    
    def __init__(self, model_name: str, api_key: str = ""):
        config = get_config_manager()
        super().__init__(
            model_name=model_name,
            api_key=api_key or config.get_anthropic_key()
        )
    
    @with_retry(max_retries=3, base_delay=1.0, backoff=2.0)
    def chat(self, system_prompt: str, history_messages: List[Dict]) -> str:
        if not HAS_ANTHROPIC:
            # 回退到 HTTP 请求方式
            return self._chat_via_http(system_prompt, history_messages)
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        # Claude 要求 messages 格式不同，需要转换
        messages = []
        for msg in history_messages:
            msg_role = msg.get('role', '')
            name = msg.get('name', 'Unknown')
            content = msg.get('content', '')
            
            if msg_role == 'narrator':
                messages.append({"role": "user", "content": f"[旁白/场景]: {content}"})
            elif name == self._current_role_name:
                messages.append({"role": "assistant", "content": content})
            else:
                messages.append({"role": "user", "content": f"[{name}]: {content}"})
        
        response = client.messages.create(
            model=self.model_name,
            max_tokens=2048,
            system=system_prompt,
            messages=messages
        )
        
        return response.content[0].text
    
    def _chat_via_http(self, system_prompt: str, history_messages: List[Dict]) -> str:
        """通过 HTTP 请求调用 Claude API"""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        messages = []
        for msg in history_messages:
            name = msg.get('name', 'Unknown')
            content = msg['content']
            messages.append({
                "role": "user",
                "content": f"[{name}]: {content}"
            })
        
        payload = {
            "model": self.model_name,
            "max_tokens": 2048,
            "system": system_prompt,
            "messages": messages
        }
        
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['content'][0]['text']
            else:
                raise Exception(f"Claude Error: {response.text}")
        except Exception as e:
            return f"[系统错误]: {str(e)}"
    
    def test_connection(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, "API Key 未配置"
        
        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model_name,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}]
            }
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "连接成功"
            else:
                return False, f"错误: {response.status_code}"
        except Exception as e:
            return False, str(e)


class OllamaInterface(BaseLLMInterface):
    """Ollama 本地模型接口"""
    
    def __init__(self, model_name: str, base_url: str = ""):
        config = get_config_manager()
        super().__init__(
            model_name=model_name,
            base_url=base_url or config.get_ollama_url()
        )
    
    @with_retry(max_retries=3, base_delay=1.0, backoff=2.0)
    def chat(self, system_prompt: str, history_messages: List[Dict]) -> str:
        formatted_msgs = self._format_history_for_chat(system_prompt, history_messages)
        
        payload = {
            "model": self.model_name,
            "messages": formatted_msgs,
            "stream": False,
            "options": {"temperature": 0.7}
        }
        
        url = f"{self.base_url.rstrip('/')}/api/chat"
        response = requests.post(url, json=payload, timeout=120)
        
        if response.status_code == 200:
            return response.json()['message']['content']
        else:
            raise Exception(f"Ollama Error: {response.text}")
    
    def test_connection(self) -> tuple[bool, str]:
        try:
            url = f"{self.base_url.rstrip('/')}/api/tags"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                return True, f"连接成功，发现 {len(models)} 个模型"
            else:
                return False, f"错误: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到 Ollama 服务"
        except Exception as e:
            return False, str(e)


def get_ollama_models(base_url: str = None) -> List[str]:
    """获取 Ollama 可用模型列表"""
    if base_url is None:
        config = get_config_manager()
        base_url = config.get_ollama_url()
    
    try:
        response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
    except Exception as e:
        print(f"无法连接 Ollama: {e}")
    return []


class ModelInterface:
    """
    统一模型接口 - 工厂模式
    根据类型创建对应的 LLM 接口实例
    """
    
    def __init__(self, model_type: str, model_name: str, 
                 api_key: str = "", base_url: str = ""):
        """
        Args:
            model_type: 模型类型 (dashscope, openai, anthropic, ollama, custom)
            model_name: 模型名称
            api_key: API Key（可选，默认从配置读取）
            base_url: API Base URL（可选，用于自定义端点）
        """
        self.model_type = model_type
        self.model_name = model_name
        self._interface = self._create_interface(model_type, model_name, api_key, base_url)
    
    def _create_interface(self, model_type: str, model_name: str,
                          api_key: str, base_url: str) -> BaseLLMInterface:
        """创建对应的接口实例"""
        if model_type == "dashscope":
            return DashScopeInterface(model_name, api_key)
        elif model_type == "openai":
            return OpenAIInterface(model_name, api_key, base_url)
        elif model_type == "anthropic":
            return AnthropicInterface(model_name, api_key)
        elif model_type == "ollama":
            return OllamaInterface(model_name, base_url)
        elif model_type.startswith("custom_"):
            # 自定义 OpenAI 兼容服务
            return OpenAIInterface(model_name, api_key, base_url)
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
    
    def chat(self, system_prompt: str, history_messages: List[Dict]) -> str:
        """发送对话请求"""
        return self._interface.chat(system_prompt, history_messages)
    
    def test_connection(self) -> tuple[bool, str]:
        """测试连接"""
        return self._interface.test_connection()
    
    def set_current_role(self, role_name: str):
        """设置当前角色名（用于消息格式化时区分自己和他人）"""
        self._interface.set_current_role(role_name)


# ================== 兼容旧代码 ==================
# 保持向后兼容性

DEFAULT_DASHSCOPE_KEY = get_config_manager().get_dashscope_key()
OLLAMA_BASE_URL = get_config_manager().get_ollama_url()