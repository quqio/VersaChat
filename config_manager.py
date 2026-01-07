# -*- coding: utf-8 -*-
"""
VersaChat 配置管理器
负责管理双层 API Key（系统层 + 用户层）和用户偏好设置
"""

import os
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

load_dotenv()

# 配置文件路径
CONFIG_DIR = Path(__file__).parent / "config"
USER_CONFIG_FILE = CONFIG_DIR / "user_config.encrypted"
SALT_FILE = CONFIG_DIR / ".salt"

# 默认加密密钥（生产环境应由用户设置）
DEFAULT_SECRET = "versachat_default_key_2024"


@dataclass
class APIProvider:
    """API 提供商配置"""
    name: str
    api_key: str = ""
    base_url: str = ""
    enabled: bool = True
    models: list = field(default_factory=list)


@dataclass
class UserConfig:
    """用户配置数据结构"""
    # API Keys (用户层)
    dashscope_key: str = ""
    openai_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_key: str = ""
    ollama_url: str = ""
    
    # 自定义 OpenAI 兼容服务
    custom_providers: Dict[str, Dict] = field(default_factory=dict)
    
    # 用户偏好
    default_temperature: float = 0.7
    default_max_tokens: int = 2048
    theme: str = "auto"  # auto, light, dark
    language: str = "zh"


class ConfigManager:
    """
    配置管理器 - 双层架构
    
    系统层: 从 .env 文件读取（部署人员配置）
    用户层: 从加密配置文件读取（用户自定义，优先级更高）
    """
    
    def __init__(self, secret: str = DEFAULT_SECRET):
        self._secret = secret
        self._fernet = self._init_encryption()
        self._user_config: Optional[UserConfig] = None
        self._ensure_config_dir()
        self._load_user_config()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    def _init_encryption(self) -> Fernet:
        """初始化加密器"""
        # 获取或创建 salt
        if SALT_FILE.exists():
            salt = SALT_FILE.read_bytes()
        else:
            salt = os.urandom(16)
            self._ensure_config_dir()
            SALT_FILE.write_bytes(salt)
        
        # 使用 PBKDF2 派生密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._secret.encode()))
        return Fernet(key)
    
    def _load_user_config(self):
        """加载用户配置"""
        if USER_CONFIG_FILE.exists():
            try:
                encrypted_data = USER_CONFIG_FILE.read_bytes()
                decrypted_data = self._fernet.decrypt(encrypted_data)
                config_dict = json.loads(decrypted_data.decode('utf-8'))
                self._user_config = UserConfig(**config_dict)
            except Exception as e:
                print(f"[ConfigManager] 加载用户配置失败: {e}")
                self._user_config = UserConfig()
        else:
            self._user_config = UserConfig()
    
    def save_user_config(self):
        """保存用户配置（加密）"""
        try:
            config_dict = asdict(self._user_config)
            json_data = json.dumps(config_dict, ensure_ascii=False)
            encrypted_data = self._fernet.encrypt(json_data.encode('utf-8'))
            USER_CONFIG_FILE.write_bytes(encrypted_data)
            return True
        except Exception as e:
            print(f"[ConfigManager] 保存用户配置失败: {e}")
            return False
    
    # ========== 系统层配置（只读） ==========

    def _get_system_config(self, key: str, default: str = "") -> str:
        """从 Streamlit Secrets 或环境变量获取系统配置"""
        # 1. 尝试从 Streamlit Secrets 读取
        try:
            import streamlit as st
            if key in st.secrets:
                return st.secrets[key]
        except:
            pass
            
        # 2. 从环境变量读取
        return os.getenv(key, default)
    
    @property
    def system_dashscope_key(self) -> str:
        """系统层 DashScope Key"""
        return self._get_system_config("DASHSCOPE_API_KEY")
    
    @property
    def system_openai_key(self) -> str:
        """系统层 OpenAI Key"""
        return self._get_system_config("OPENAI_API_KEY")
    
    @property
    def system_openai_base_url(self) -> str:
        """系统层 OpenAI Base URL"""
        return self._get_system_config("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    @property
    def system_anthropic_key(self) -> str:
        """系统层 Anthropic Key"""
        return self._get_system_config("ANTHROPIC_API_KEY")
    
    @property
    def system_ollama_url(self) -> str:
        """系统层 Ollama URL"""
        return self._get_system_config("OLLAMA_URL", "http://localhost:11434")
    
    # ========== 合并配置（用户层优先） ==========
    
    def get_dashscope_key(self) -> str:
        """获取 DashScope Key（用户层优先）"""
        return self._user_config.dashscope_key or self.system_dashscope_key
    
    def get_openai_key(self) -> str:
        """获取 OpenAI Key（用户层优先）"""
        return self._user_config.openai_key or self.system_openai_key
    
    def get_openai_base_url(self) -> str:
        """获取 OpenAI Base URL（用户层优先）"""
        return self._user_config.openai_base_url or self.system_openai_base_url
    
    def get_anthropic_key(self) -> str:
        """获取 Anthropic Key（用户层优先）"""
        return self._user_config.anthropic_key or self.system_anthropic_key
    
    def get_ollama_url(self) -> str:
        """获取 Ollama URL（用户层优先）"""
        return self._user_config.ollama_url or self.system_ollama_url
    
    # ========== 用户层配置（可写） ==========
    
    def set_user_dashscope_key(self, key: str):
        self._user_config.dashscope_key = key
        self.save_user_config()
    
    def set_user_openai_key(self, key: str):
        self._user_config.openai_key = key
        self.save_user_config()
    
    def set_user_openai_base_url(self, url: str):
        self._user_config.openai_base_url = url
        self.save_user_config()
    
    def set_user_anthropic_key(self, key: str):
        self._user_config.anthropic_key = key
        self.save_user_config()
    
    def set_user_ollama_url(self, url: str):
        self._user_config.ollama_url = url
        self.save_user_config()
    
    # ========== 自定义提供商 ==========
    
    def add_custom_provider(self, name: str, api_key: str, base_url: str, models: list = None):
        """添加自定义 OpenAI 兼容服务"""
        self._user_config.custom_providers[name] = {
            "api_key": api_key,
            "base_url": base_url,
            "models": models or []
        }
        self.save_user_config()
    
    def remove_custom_provider(self, name: str):
        """移除自定义提供商"""
        if name in self._user_config.custom_providers:
            del self._user_config.custom_providers[name]
            self.save_user_config()
    
    def get_custom_providers(self) -> Dict[str, Dict]:
        """获取所有自定义提供商"""
        return self._user_config.custom_providers.copy()
    
    # ========== 可用提供商列表 ==========
    
    def get_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """获取所有可用的 API 提供商"""
        providers = {}
        
        # DashScope
        if self.get_dashscope_key():
            providers["dashscope"] = {
                "name": "阿里 DashScope",
                "available": True,
                "source": "user" if self._user_config.dashscope_key else "system",
                "models": [
                    "qwen-max", "qwen-plus", "qwen-turbo", "qwen-long",
                    "qwen-coder-plus", "qwen-coder-turbo",
                    "qwen2.5-72b-instruct", "qwen2.5-32b-instruct",
                    "qwen2.5-14b-instruct", "qwen2.5-7b-instruct"
                ]
            }
        
        # OpenAI
        if self.get_openai_key():
            providers["openai"] = {
                "name": "OpenAI",
                "available": True,
                "source": "user" if self._user_config.openai_key else "system",
                "base_url": self.get_openai_base_url(),
                "models": [
                    "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4",
                    "gpt-3.5-turbo", "o1-preview", "o1-mini"
                ]
            }
        
        # Anthropic
        if self.get_anthropic_key():
            providers["anthropic"] = {
                "name": "Anthropic Claude",
                "available": True,
                "source": "user" if self._user_config.anthropic_key else "system",
                "models": [
                    "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022",
                    "claude-3-opus-20240229", "claude-3-sonnet-20240229"
                ]
            }
        
        # Ollama
        ollama_url = self.get_ollama_url()
        if ollama_url:
            providers["ollama"] = {
                "name": "Ollama (本地)",
                "available": True,  # 实际可用性需要运行时检测
                "source": "user" if self._user_config.ollama_url else "system",
                "base_url": ollama_url,
                "models": []  # 动态获取
            }
        
        # 自定义提供商
        for name, config in self._user_config.custom_providers.items():
            providers[f"custom_{name}"] = {
                "name": name,
                "available": True,
                "source": "user",
                "base_url": config["base_url"],
                "models": config.get("models", [])
            }
        
        return providers
    
    # ========== 用户偏好 ==========
    
    @property
    def default_temperature(self) -> float:
        return self._user_config.default_temperature
    
    @default_temperature.setter
    def default_temperature(self, value: float):
        self._user_config.default_temperature = max(0.0, min(2.0, value))
        self.save_user_config()
    
    @property
    def theme(self) -> str:
        return self._user_config.theme
    
    @theme.setter
    def theme(self, value: str):
        if value in ("auto", "light", "dark"):
            self._user_config.theme = value
            self.save_user_config()
    
    # ========== 工具方法 ==========
    
    def mask_key(self, key: str, show_chars: int = 4) -> str:
        """脱敏显示 API Key"""
        if not key or len(key) < show_chars * 2:
            return "***"
        return f"{key[:show_chars]}...{key[-show_chars:]}"
    
    def has_any_api_key(self) -> bool:
        """检查是否配置了任何 API Key"""
        return bool(
            self.get_dashscope_key() or 
            self.get_openai_key() or 
            self.get_anthropic_key() or
            self.get_ollama_url()
        )


# 全局单例
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """获取配置管理器单例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
