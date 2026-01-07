# -*- coding: utf-8 -*-
"""
VersaChat - 多角色 AI 对话平台
主应用入口
"""

import streamlit as st
import time
import uuid
from datetime import datetime

# 导入核心模块
from config_manager import get_config_manager
from templates import get_template_manager, SceneTemplate, RoleTemplate
from llm_backend import ModelInterface, get_ollama_models
from context_manager import (
    get_context_manager, 
    get_memory_manager, 
    get_flow_controller,
    TokenEstimator
)
import session_manager

# ================== 页面配置 ==================
# Logo 路径
LOGO_PATH = "static/logo.png"

st.set_page_config(
    page_title="VersaChat - 多角色AI对话",
    page_icon=LOGO_PATH,  # 使用自定义 Logo
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================== 样式定义 ==================
ROLE_COLORS = [
    "#FF6B6B",  # 珊瑚红
    "#4ECDC4",  # 青绿色
    "#45B7D1",  # 天空蓝
    "#96CEB4",  # 薄荷绿
    "#FFEAA7",  # 柠檬黄
    "#DDA0DD",  # 梅红色
    "#98D8C8",  # 浅绿色
    "#F7DC6F",  # 金色
]

def get_role_color(index: int) -> str:
    return ROLE_COLORS[index % len(ROLE_COLORS)]

# 自定义 CSS - 清新淡雅风格
st.markdown("""
<style>
    /* ============================================
       VersaChat 清新淡雅风格 UI 样式系统
       设计理念: 自然、清新、舒适、专业
       ============================================ */
    
    /* === 1. CSS 变量定义 === */
    :root {
        /* 背景色系 - 米白到浅灰 */
        --vc-bg-primary: #fafbfc;
        --vc-bg-secondary: #f0f2f5;
        --vc-bg-card: #ffffff;
        --vc-bg-hover: #f5f7fa;
        
        /* 品牌色 - 薄荷绿系 */
        --vc-brand-primary: #10b981;
        --vc-brand-light: #d1fae5;
        --vc-brand-dark: #059669;
        --vc-brand-gradient: linear-gradient(135deg, #10b981 0%, #34d399 100%);
        
        /* 辅助色 */
        --vc-accent: #6366f1;
        --vc-accent-light: #e0e7ff;
        
        /* 语义色 */
        --vc-success: #10b981;
        --vc-warning: #f59e0b;
        --vc-error: #ef4444;
        --vc-info: #3b82f6;
        
        /* 文字色 */
        --vc-text-primary: #1f2937;
        --vc-text-secondary: #4b5563;
        --vc-text-muted: #9ca3af;
        
        /* 边框 */
        --vc-border: #e5e7eb;
        --vc-border-hover: #d1d5db;
        
        /* 圆角 */
        --vc-radius-sm: 8px;
        --vc-radius-md: 12px;
        --vc-radius-lg: 16px;
        --vc-radius-xl: 24px;
        
        /* 阴影 - 更柔和 */
        --vc-shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
        --vc-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        --vc-shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.08);
    }
    
    /* === 2. 全局样式 === */
    .stApp {
        background: var(--vc-bg-primary);
    }
    
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1200px;
    }
    
    /* 隐藏 Streamlit 默认元素 */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* === 3. 侧边栏 === */
    [data-testid="stSidebar"] {
        background: var(--vc-bg-card);
        border-right: 1px solid var(--vc-border);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: var(--vc-text-primary);
    }
    
    /* 侧边栏品牌标识 */
    .sidebar-brand {
        text-align: center;
        padding: 1.5rem 1rem;
        border-bottom: 1px solid var(--vc-border);
        margin-bottom: 1.5rem;
        background: linear-gradient(180deg, var(--vc-brand-light) 0%, var(--vc-bg-card) 100%);
    }
    
    .sidebar-brand h1 {
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
        color: var(--vc-brand-dark);
    }
    
    .sidebar-brand p {
        margin: 0.3rem 0 0;
        font-size: 0.85rem;
        color: var(--vc-text-muted);
    }
    
    /* === 4. 按钮样式 === */
    .stButton > button {
        border-radius: var(--vc-radius-md) !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        border: 1px solid var(--vc-border) !important;
        background: var(--vc-bg-card) !important;
        color: var(--vc-text-primary) !important;
    }
    
    .stButton > button:hover {
        border-color: var(--vc-brand-primary) !important;
        background: var(--vc-bg-hover) !important;
        box-shadow: var(--vc-shadow) !important;
    }
    
    .stButton > button[kind="primary"] {
        background: var(--vc-brand-gradient) !important;
        border: none !important;
        color: white !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        opacity: 0.9;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3) !important;
        transform: translateY(-1px);
    }
    
    /* === 5. 输入框样式 === */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        background: var(--vc-bg-card) !important;
        border: 1.5px solid var(--vc-border) !important;
        border-radius: var(--vc-radius-md) !important;
        color: var(--vc-text-primary) !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--vc-brand-primary) !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15) !important;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: var(--vc-text-muted) !important;
    }
    
    /* === 6. Expander 样式 === */
    .streamlit-expanderHeader {
        background: var(--vc-bg-card) !important;
        border-radius: var(--vc-radius-md) !important;
        border: 1px solid var(--vc-border) !important;
        color: var(--vc-text-primary) !important;
        font-weight: 500 !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--vc-bg-hover) !important;
    }
    
    .streamlit-expanderContent {
        background: var(--vc-bg-secondary) !important;
        border: 1px solid var(--vc-border) !important;
        border-top: none !important;
        border-radius: 0 0 var(--vc-radius-md) var(--vc-radius-md) !important;
    }
    
    /* === 7. 对话气泡 - 角色消息 === */
    .chat-bubble {
        background: var(--vc-bg-card);
        border-radius: var(--vc-radius-lg);
        padding: 16px 20px;
        margin-bottom: 14px;
        border-left: 4px solid;
        box-shadow: var(--vc-shadow);
        transition: all 0.2s ease;
    }
    
    .chat-bubble:hover {
        box-shadow: var(--vc-shadow-lg);
        transform: translateY(-2px);
    }
    
    .chat-bubble .role-name {
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .chat-bubble .content {
        line-height: 1.7;
        white-space: pre-wrap;
        color: var(--vc-text-secondary);
        font-size: 0.95rem;
    }
    
    /* === 8. 对话气泡 - 旁白消息 === */
    .narrator-bubble {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        color: var(--vc-text-primary);
        padding: 16px 24px;
        border-radius: var(--vc-radius-lg);
        margin-bottom: 14px;
        text-align: center;
        border: 1px solid #bbf7d0;
        box-shadow: var(--vc-shadow-sm);
    }
    
    .narrator-bubble .narrator-label {
        font-weight: 600;
        font-size: 0.8rem;
        color: var(--vc-brand-dark);
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .narrator-bubble .narrator-content {
        font-size: 0.95rem;
        line-height: 1.6;
        color: var(--vc-text-secondary);
        font-style: italic;
    }
    
    /* === 9. 角色卡片 === */
    .role-card {
        background: var(--vc-bg-card);
        border-radius: var(--vc-radius-md);
        padding: 12px 16px;
        margin-bottom: 8px;
        border-left: 4px solid;
        box-shadow: var(--vc-shadow-sm);
        transition: all 0.2s ease;
    }
    
    .role-card:hover {
        box-shadow: var(--vc-shadow);
        transform: translateX(4px);
    }
    
    /* === 10. 状态指示器 === */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .status-idle {
        background: var(--vc-bg-secondary);
        color: var(--vc-text-muted);
    }
    
    .status-running {
        background: var(--vc-brand-light);
        color: var(--vc-brand-dark);
        animation: gentle-pulse 2s infinite;
    }
    
    .status-paused {
        background: #fef3c7;
        color: #d97706;
    }
    
    @keyframes gentle-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* === 11. 场景标题 === */
    .scene-title {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: var(--vc-text-primary);
    }
    
    .scene-title .emoji {
        margin-right: 8px;
    }
    
    /* === 12. 分割线 === */
    hr {
        border: none;
        height: 1px;
        background: var(--vc-border);
        margin: 1.5rem 0;
    }
    
    /* === 13. 滚动条 === */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--vc-bg-secondary);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #d1d5db;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #9ca3af;
    }
    
    /* === 14. 聊天容器 === */
    [data-testid="stVerticalBlock"] > div:has(.chat-bubble) {
        background: var(--vc-bg-secondary);
        border-radius: var(--vc-radius-lg);
        padding: 16px;
    }
    
    /* === 15. Toast 通知 === */
    .stToast {
        background: var(--vc-bg-card) !important;
        border: 1px solid var(--vc-border) !important;
        border-radius: var(--vc-radius-md) !important;
        box-shadow: var(--vc-shadow-lg) !important;
    }
    
    /* === 16. 警告和信息框 === */
    .stAlert {
        border-radius: var(--vc-radius-md) !important;
    }
    
    /* === 17. 容器样式 === */
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
        background: transparent;
    }
    
    div[data-testid="stExpander"] details {
        border: none !important;
    }
    
    /* === 18. 标签和徽章 === */
    .tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 500;
        background: var(--vc-bg-secondary);
        color: var(--vc-text-muted);
    }
    
    .tag-primary {
        background: var(--vc-brand-light);
        color: var(--vc-brand-dark);
    }
    
    /* === 19. 链接样式 === */
    a {
        color: var(--vc-brand-primary);
        text-decoration: none;
    }
    
    a:hover {
        color: var(--vc-brand-dark);
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# ================== 状态初始化 ==================
def init_session_state():
    """初始化所有 session state（含多用户隔离）"""
    
    # 为每个浏览器会话生成唯一的用户标识
    if "_user_id" not in st.session_state:
        import uuid
        st.session_state._user_id = str(uuid.uuid4())[:8]
    
    # 会话 ID 包含用户标识前缀，避免多用户冲突
    user_prefix = st.session_state._user_id
    
    defaults = {
        "session_id": f"{user_prefix}_{session_manager.generate_session_id()[:8]}",
        "session_name": "新场景",
        "roles": [],  # 角色列表
        "chat_history": [],  # 对话历史
        "status": "IDLE",  # IDLE, RUNNING, PAUSED
        "turn_index": 0,
        "round_count": 0,
        "max_rounds": 50,
        "show_settings": False,
        "show_template_picker": False,
        "editing_role_index": None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ================== 多用户隔离：每个浏览器会话独立的配置管理器 ==================
def get_session_config_manager():
    """获取当前会话的配置管理器（多用户隔离）"""
    if "_config_manager" not in st.session_state:
        st.session_state._config_manager = get_config_manager()
    return st.session_state._config_manager

config_manager = get_session_config_manager()
template_manager = get_template_manager()

# ================== 辅助函数 ==================
def trigger_autosave():
    """触发自动保存"""
    session_manager.autosave_session(
        st.session_state.session_id,
        st.session_state.session_name
    )

def apply_template(template: SceneTemplate):
    """应用场景模板"""
    # 重置状态 - 包含用户标识前缀
    user_prefix = st.session_state._user_id
    st.session_state.session_id = f"{user_prefix}_{session_manager.generate_session_id()[:8]}"
    st.session_state.session_name = template.name
    st.session_state.chat_history = []
    st.session_state.turn_index = 0
    st.session_state.round_count = 0
    st.session_state.status = "IDLE"
    
    # 添加角色
    st.session_state.roles = []
    for i, role_template in enumerate(template.roles):
        role = {
            "name": role_template.name,
            "persona": role_template.persona,
            "type": role_template.provider,
            "model": role_template.model,
            "color": role_template.color or get_role_color(i),
            "interface": ModelInterface(role_template.provider, role_template.model)
        }
        st.session_state.roles.append(role)
    
    # 添加开场旁白
    if template.opening_narration:
        st.session_state.chat_history.append({
            "role": "narrator",
            "name": "旁白",
            "content": template.opening_narration
        })
    
    trigger_autosave()

def get_available_models(provider: str) -> list:
    """获取指定提供商的可用模型列表"""
    providers = config_manager.get_available_providers()
    
    if provider == "ollama":
        # 缓存 Ollama 模型列表，避免每次刷新重新获取导致顺序变化
        cache_key = "_ollama_models_cache"
        if cache_key not in st.session_state:
            st.session_state[cache_key] = get_ollama_models()
        return st.session_state[cache_key]
    elif provider in providers:
        return providers[provider].get("models", [])
    return []

def refresh_ollama_models():
    """刷新 Ollama 模型缓存"""
    st.session_state["_ollama_models_cache"] = get_ollama_models()

# ================== 侧边栏 ==================
with st.sidebar:
    # 产品标题 - 品牌标识 + Logo
    col_logo, col_title = st.columns([1, 3])
    with col_logo:
        try:
            st.image(LOGO_PATH, width=50)
        except:
            st.markdown("🎭", unsafe_allow_html=True)
    with col_title:
        st.markdown("""
        <div style="padding-top: 8px;">
            <h3 style="margin: 0; color: #059669;">VersaChat</h3>
            <p style="margin: 0; font-size: 0.75rem; color: #9ca3af;">多角色 AI 对话平台</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========== 场景管理 ==========
    st.markdown("### 📍 场景管理")
    
    # 新建场景按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ 新建场景", use_container_width=True, type="primary"):
            user_prefix = st.session_state._user_id
            st.session_state.session_id = f"{user_prefix}_{session_manager.generate_session_id()[:8]}"
            st.session_state.session_name = "新场景"
            st.session_state.roles = []
            st.session_state.chat_history = []
            st.session_state.turn_index = 0
            st.session_state.round_count = 0
            st.session_state.status = "IDLE"
            st.rerun()
    
    with col2:
        if st.button("📂 场景模板", use_container_width=True):
            st.session_state.show_template_picker = not st.session_state.show_template_picker
    
    # 模板选择器
    if st.session_state.show_template_picker:
        st.markdown("---")
        st.markdown("##### 🎬 选择场景模板")
        
        # 按分类显示模板
        categories = template_manager.get_categories()
        selected_category = st.selectbox("分类", ["全部"] + categories, label_visibility="collapsed")
        
        if selected_category == "全部":
            templates = template_manager.get_all_templates()
        else:
            templates = template_manager.get_templates_by_category(selected_category)
        
        for template in templates:
            with st.container(border=True):
                st.markdown(f"**{template.name}**")
                st.caption(template.description)
                st.caption(f"👥 {len(template.roles)} 个角色 | 🏷️ {template.category}")
                if st.button("使用此模板", key=f"use_{template.id}", use_container_width=True):
                    apply_template(template)
                    st.session_state.show_template_picker = False
                    st.rerun()
        
        st.markdown("---")
    
    # 当前场景名称
    new_name = st.text_input("场景名称", value=st.session_state.session_name, label_visibility="collapsed")
    if new_name != st.session_state.session_name:
        st.session_state.session_name = new_name
        trigger_autosave()
    
    # 历史场景
    with st.expander("🕒 历史场景", expanded=False):
        all_sessions = session_manager.get_all_sessions()
        user_prefix = st.session_state._user_id
        current_session_id = st.session_state.session_id
        
        # 分类会话：当前用户的 vs 旧格式（共享）
        my_sessions = []
        shared_sessions = []
        current_session_in_list = False
        
        for s in all_sessions:
            if s["id"] == current_session_id:
                current_session_in_list = True
            if s["id"].startswith(user_prefix):
                my_sessions.append(s)
            elif "_" not in s["id"]:  # 旧格式UUID（无下划线前缀）
                shared_sessions.append(s)
        
        # 如果当前会话不在列表中（新创建的还未保存），手动添加
        if not current_session_in_list and st.session_state.roles:
            my_sessions.insert(0, {
                "id": current_session_id,
                "name": st.session_state.session_name,
                "last_modified": "当前会话",
                "role_count": len(st.session_state.roles)
            })
        
        # 显示切换
        show_shared = st.checkbox("显示共享/旧版会话", value=False, key="show_shared_sessions")
        
        display_sessions = my_sessions + (shared_sessions if show_shared else [])
        
        if not display_sessions:
            st.caption("暂无历史场景" if not shared_sessions else "暂无您的场景，可勾选上方选项查看共享场景")
        
        for sess in display_sessions:
            is_active = (sess["id"] == current_session_id)
            is_shared = "_" not in sess["id"]
            
            # 状态指示
            if is_active:
                prefix = "🟢 "  # 当前活动
            elif is_shared:
                prefix = "📤 "  # 共享
            else:
                prefix = ""
            
            btn_label = f"{prefix}{sess['name']}"
            
            col_name, col_del = st.columns([5, 1])
            if col_name.button(btn_label, key=f"load_{sess['id']}", 
                              use_container_width=True, disabled=is_active):
                # 切换前保存当前会话
                trigger_autosave()
                success, msg = session_manager.load_session(sess["id"])
                if success:
                    st.rerun()
            
            if col_del.button("🗑️", key=f"del_{sess['id']}", help="删除"):
                session_manager.delete_session(sess["id"])
                if is_active:
                    st.session_state.session_id = f"{user_prefix}_{session_manager.generate_session_id()[:8]}"
                    st.session_state.roles = []
                    st.session_state.chat_history = []
                st.rerun()
    
    st.markdown("---")
    
    # ========== 角色工坊 ==========
    st.markdown("### 🎨 角色工坊")
    
    with st.expander("➕ 添加新角色", expanded=len(st.session_state.roles) == 0):
        # 角色名称
        role_name = st.text_input("角色名称", value="", key="new_role_name", 
                                   placeholder="例如：苏格拉底")
        
        # 模型来源选择
        providers = config_manager.get_available_providers()
        provider_names = {
            "dashscope": "🌐 阿里 DashScope",
            "openai": "🤖 OpenAI",
            "anthropic": "🧠 Anthropic Claude",
            "ollama": "💻 Ollama (本地)"
        }
        
        available_providers = []
        for key in ["dashscope", "openai", "anthropic", "ollama"]:
            if key in providers:
                available_providers.append((key, provider_names.get(key, key)))
        
        if not available_providers:
            st.warning("⚠️ 未配置任何 API Key，请先在设置中配置")
        else:
            provider_options = [p[1] for p in available_providers]
            provider_keys = [p[0] for p in available_providers]
            
            selected_provider_name = st.selectbox("模型来源", provider_options, key="new_role_provider")
            selected_provider = provider_keys[provider_options.index(selected_provider_name)]
            
            # 模型选择
            available_models = get_available_models(selected_provider)
            if available_models:
                selected_model = st.selectbox("选择模型", available_models, key="new_role_model")
            else:
                selected_model = st.text_input("模型名称", key="new_role_model_input", 
                                               placeholder="输入模型名称")
            
            # 人格设定
            role_persona = st.text_area("人格设定", height=120, key="new_role_persona",
                                        placeholder="描述这个角色的性格、背景、说话风格...")
            
            if st.button("✨ 添加角色", use_container_width=True, type="primary"):
                if not role_name:
                    st.error("请输入角色名称")
                elif not role_persona:
                    st.error("请输入人格设定")
                else:
                    model_name = selected_model if available_models else st.session_state.get("new_role_model_input", "")
                    if not model_name:
                        st.error("请选择或输入模型名称")
                    else:
                        new_role = {
                            "name": role_name,
                            "persona": role_persona,
                            "type": selected_provider,
                            "model": model_name,
                            "color": get_role_color(len(st.session_state.roles)),
                            "interface": ModelInterface(selected_provider, model_name)
                        }
                        st.session_state.roles.append(new_role)
                        trigger_autosave()
                        st.toast(f"✅ 角色 {role_name} 已添加")
                        time.sleep(0.3)
                        st.rerun()
    
    # 当前角色列表
    if st.session_state.roles:
        st.markdown(f"##### 当前角色 ({len(st.session_state.roles)})")
        
        for idx, role in enumerate(st.session_state.roles):
            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 1, 1])
                
                with col1:
                    st.markdown(f"""
                    <div style="border-left: 3px solid {role['color']}; padding-left: 8px;">
                        <strong>{role['name']}</strong><br/>
                        <span style="opacity: 0.7; font-size: 0.85em;">🤖 {role['model']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # 对话进行中禁止编辑
                    edit_disabled = st.session_state.status == "RUNNING"
                    if st.button("✏️", key=f"edit_role_{idx}", help="编辑角色" if not edit_disabled else "对话中无法编辑", disabled=edit_disabled):
                        st.session_state.editing_role_index = idx
                
                with col3:
                    # 对话进行中禁止删除
                    del_disabled = st.session_state.status == "RUNNING"
                    if st.button("❌", key=f"del_role_{idx}", help="删除角色" if not del_disabled else "对话中无法删除", disabled=del_disabled):
                        st.session_state.roles.pop(idx)
                        trigger_autosave()
                        st.rerun()
        
        # 编辑角色弹窗
        if st.session_state.editing_role_index is not None:
            idx = st.session_state.editing_role_index
            if idx < len(st.session_state.roles):
                role = st.session_state.roles[idx]
                
                # 对话进行中自动关闭编辑面板
                if st.session_state.status == "RUNNING":
                    st.session_state.editing_role_index = None
                    st.warning("⚠️ 对话进行中无法编辑角色")
                else:
                    st.markdown("---")
                    st.markdown(f"##### ✏️ 编辑角色: {role['name']}")
                    
                    # 使用包含索引的唯一 key，避免 Streamlit 复用缓存值
                    edit_key_suffix = f"_{idx}_{role['name']}"
                    
                    # 名称
                    edited_name = st.text_input(
                        "名称", 
                        value=role['name'], 
                        key=f"edit_name{edit_key_suffix}"
                    )
                    
                    # 模型来源选择
                    providers = config_manager.get_available_providers()
                    provider_names = {
                        "dashscope": "🌐 阿里 DashScope",
                        "openai": "🤖 OpenAI",
                        "anthropic": "🧠 Anthropic Claude",
                        "ollama": "💻 Ollama (本地)"
                    }
                    
                    available_providers = []
                    for key in ["dashscope", "openai", "anthropic", "ollama"]:
                        if key in providers:
                            available_providers.append((key, provider_names.get(key, key)))
                    
                    if available_providers:
                        provider_options = [p[1] for p in available_providers]
                        provider_keys = [p[0] for p in available_providers]
                        
                        # 找到当前角色的模型来源索引
                        current_provider = role.get('type', 'dashscope')
                        try:
                            current_idx = provider_keys.index(current_provider)
                        except ValueError:
                            current_idx = 0
                        
                        selected_provider_name = st.selectbox(
                            "模型来源", 
                            provider_options, 
                            index=current_idx,
                            key=f"edit_provider{edit_key_suffix}"
                        )
                        selected_provider = provider_keys[provider_options.index(selected_provider_name)]
                        
                        # 模型选择
                        # 重要：将 provider 加入 key，切换来源时重置模型选择
                        available_models = get_available_models(selected_provider)
                        model_key = f"edit_model{edit_key_suffix}_{selected_provider}"
                        
                        if available_models:
                            # 仅当模型来源未变化时，尝试匹配当前模型
                            current_model = role.get('model', '')
                            if role.get('type') == selected_provider and current_model in available_models:
                                model_idx = available_models.index(current_model)
                            else:
                                model_idx = 0  # 来源变化了，默认选第一个
                            
                            edited_model = st.selectbox(
                                "选择模型", 
                                available_models, 
                                index=model_idx,
                                key=model_key
                            )
                        else:
                            # 无预设模型列表时，使用文本输入
                            default_model = role.get('model', '') if role.get('type') == selected_provider else ''
                            edited_model = st.text_input(
                                "模型名称", 
                                value=default_model,
                                key=f"edit_model_input{edit_key_suffix}_{selected_provider}",
                                placeholder="输入模型名称"
                            )
                    else:
                        selected_provider = role.get('type', 'dashscope')
                        edited_model = role.get('model', '')
                        st.warning("⚠️ 未配置任何 API Key")
                    
                    # 人格设定
                    edited_persona = st.text_area(
                        "人格设定", 
                        value=role['persona'], 
                        height=150, 
                        key=f"edit_persona{edit_key_suffix}"
                    )
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 保存", use_container_width=True, type="primary", key=f"save_edit{edit_key_suffix}"):
                            final_model = edited_model if available_models else st.session_state.get(f"edit_model_input{edit_key_suffix}", edited_model)
                            
                            st.session_state.roles[idx]["name"] = edited_name
                            st.session_state.roles[idx]["persona"] = edited_persona
                            st.session_state.roles[idx]["type"] = selected_provider
                            st.session_state.roles[idx]["model"] = final_model
                            st.session_state.roles[idx]["interface"] = ModelInterface(selected_provider, final_model)
                            
                            st.session_state.editing_role_index = None
                            trigger_autosave()
                            st.toast("✅ 角色已更新")
                            st.rerun()
                    
                    with col_cancel:
                        if st.button("取消", use_container_width=True, key=f"cancel_edit{edit_key_suffix}"):
                            st.session_state.editing_role_index = None
                            st.rerun()
    
    st.markdown("---")
    
    # ========== 设置 ==========
    st.markdown("### ⚙️ 设置")
    
    with st.expander("🔑 API 配置", expanded=False):
        st.caption("用户配置的 Key 优先级高于系统预置")
        
        # DashScope
        st.markdown("**阿里 DashScope**")
        current_ds_key = config_manager.get_dashscope_key()
        ds_display = config_manager.mask_key(current_ds_key) if current_ds_key else "未配置"
        st.caption(f"当前: {ds_display}")
        new_ds_key = st.text_input("DashScope API Key", type="password", 
                                    key="ds_key_input", label_visibility="collapsed",
                                    placeholder="输入新 Key...")
        if new_ds_key and st.button("保存 DashScope Key", key="save_ds"):
            config_manager.set_user_dashscope_key(new_ds_key)
            st.toast("✅ DashScope Key 已保存")
            st.rerun()
        
        st.markdown("---")
        
        # OpenAI
        st.markdown("**OpenAI**")
        current_oai_key = config_manager.get_openai_key()
        oai_display = config_manager.mask_key(current_oai_key) if current_oai_key else "未配置"
        st.caption(f"当前: {oai_display}")
        new_oai_key = st.text_input("OpenAI API Key", type="password",
                                     key="oai_key_input", label_visibility="collapsed",
                                     placeholder="输入新 Key...")
        if new_oai_key and st.button("保存 OpenAI Key", key="save_oai"):
            config_manager.set_user_openai_key(new_oai_key)
            st.toast("✅ OpenAI Key 已保存")
            st.rerun()
        
        new_oai_url = st.text_input("OpenAI Base URL (可选)", 
                                     value=config_manager.get_openai_base_url(),
                                     key="oai_url_input",
                                     placeholder="https://api.openai.com/v1")
        if st.button("保存 OpenAI URL", key="save_oai_url"):
            config_manager.set_user_openai_base_url(new_oai_url)
            st.toast("✅ OpenAI URL 已保存")
        
        st.markdown("---")
        
        # Anthropic
        st.markdown("**Anthropic Claude**")
        current_ant_key = config_manager.get_anthropic_key()
        ant_display = config_manager.mask_key(current_ant_key) if current_ant_key else "未配置"
        st.caption(f"当前: {ant_display}")
        new_ant_key = st.text_input("Anthropic API Key", type="password",
                                     key="ant_key_input", label_visibility="collapsed",
                                     placeholder="输入新 Key...")
        if new_ant_key and st.button("保存 Anthropic Key", key="save_ant"):
            config_manager.set_user_anthropic_key(new_ant_key)
            st.toast("✅ Anthropic Key 已保存")
            st.rerun()
        
        st.markdown("---")
        
        # Ollama
        st.markdown("**Ollama (本地)**")
        current_ollama_url = config_manager.get_ollama_url()
        st.caption(f"当前: {current_ollama_url}")
        new_ollama_url = st.text_input("Ollama URL", value=current_ollama_url,
                                        key="ollama_url_input", label_visibility="collapsed")
        col_save_ollama, col_refresh_ollama = st.columns(2)
        with col_save_ollama:
            if st.button("保存 URL", key="save_ollama", use_container_width=True):
                config_manager.set_user_ollama_url(new_ollama_url)
                refresh_ollama_models()
                st.toast("✅ Ollama URL 已保存")
                st.rerun()
        with col_refresh_ollama:
            if st.button("🔄 刷新模型", key="refresh_ollama", use_container_width=True):
                refresh_ollama_models()
                st.toast("✅ 模型列表已刷新")
                st.rerun()
    
    # 导出功能
    with st.expander("📤 导出对话", expanded=False):
        if st.session_state.chat_history:
            # Markdown 导出
            if st.button("📝 导出为 Markdown", use_container_width=True):
                md_content = session_manager.export_session_markdown(
                    st.session_state.session_name,
                    st.session_state.roles,
                    st.session_state.chat_history
                )
                st.download_button(
                    "⬇️ 下载 Markdown",
                    md_content,
                    file_name=f"{st.session_state.session_name}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            # JSON 导出
            if st.button("📊 导出为 JSON", use_container_width=True):
                json_content = session_manager.export_session_json(
                    st.session_state.session_id,
                    st.session_state.session_name,
                    st.session_state.roles,
                    st.session_state.chat_history
                )
                st.download_button(
                    "⬇️ 下载 JSON",
                    json_content,
                    file_name=f"{st.session_state.session_name}.json",
                    mime="application/json",
                    use_container_width=True
                )
        else:
            st.caption("暂无对话内容可导出")


# ================== 主界面 ==================
# 场景标题 - 专业化设计 + Logo
col_main_logo, col_main_title = st.columns([0.06, 0.94])
with col_main_logo:
    try:
        st.image(LOGO_PATH, width=42)
    except:
        pass
with col_main_title:
    st.markdown(f"""
    <h1 style="margin: 0; padding-top: 4px; color: #1f2937;">{st.session_state.session_name}</h1>
    """, unsafe_allow_html=True)

# 控制栏
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])

with col1:
    start_disabled = len(st.session_state.roles) < 2
    if st.button("▶️ 开始", type="primary", use_container_width=True, disabled=start_disabled):
        if len(st.session_state.roles) < 2:
            st.error("至少需要两个角色！")
        else:
            st.session_state.status = "RUNNING"
            if len(st.session_state.chat_history) == 0:
                st.session_state.chat_history.append({
                    "role": "narrator",
                    "name": "旁白",
                    "content": "对话开始。"
                })
            # 立即保存会话状态
            trigger_autosave()
            st.rerun()

with col2:
    if st.button("⏸️ 暂停", use_container_width=True):
        st.session_state.status = "PAUSED"
        trigger_autosave()

with col3:
    if st.button("⏹️ 重置", use_container_width=True):
        st.session_state.status = "IDLE"
        st.session_state.chat_history = []
        st.session_state.turn_index = 0
        st.session_state.round_count = 0
        trigger_autosave()
        st.rerun()

with col4:
    # 保存为模板
    if st.button("💾 存为模板", use_container_width=True):
        if st.session_state.roles:
            template = template_manager.save_as_template(
                name=st.session_state.session_name,
                description=f"自定义场景，包含 {len(st.session_state.roles)} 个角色",
                category="自定义",
                roles=[{
                    "name": r["name"],
                    "persona": r["persona"],
                    "type": r["type"],
                    "model": r["model"],
                    "color": r["color"]
                } for r in st.session_state.roles],
                opening_narration=st.session_state.chat_history[0]["content"] if st.session_state.chat_history else ""
            )
            st.toast(f"✅ 已保存为模板: {template.name}")
        else:
            st.warning("请先添加角色")

# 状态指示 - 专业化设计
status_styles = {
    "IDLE": ("status-idle", "💤 等待开始"),
    "RUNNING": ("status-running", "🔴 对话进行中"),
    "PAUSED": ("status-paused", "⏸️ 已暂停")
}
status_class, status_text = status_styles[st.session_state.status]

st.markdown(f"""
<div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
    <span class="status-indicator {status_class}">{status_text}</span>
    <span style="color: rgba(255,255,255,0.5); font-size: 0.85rem;">轮次: {st.session_state.round_count}</span>
</div>
""", unsafe_allow_html=True)

# 对话展示区
chat_container = st.container(height=450)

with chat_container:
    for msg in st.session_state.chat_history:
        if msg["role"] == "narrator":
            # 旁白消息 - 专业化设计
            st.markdown(f"""
            <div class="narrator-bubble">
                <div class="narrator-label">💬 旁白</div>
                <div class="narrator-content">{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # 角色消息
            color = "#888888"
            for role in st.session_state.roles:
                if role['name'] == msg['name']:
                    color = role.get('color', '#888888')
                    break
            
            # 角色消息 - 专业化设计
            st.markdown(f"""
            <div class="chat-bubble" style="border-left-color: {color};">
                <div class="role-name" style="color: {color};">
                    <span style="background: {color}; width: 10px; height: 10px; border-radius: 50%; display: inline-block;"></span>
                    {msg['name']}
                </div>
                <div class="content">{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)

# 旁白输入区
st.markdown("### 💬 旁白")
col_input, col_send = st.columns([5, 1])
narrator_input = col_input.text_input("输入旁白内容...", label_visibility="collapsed", 
                                       placeholder="输入旁白内容，引导对话方向...")
if col_send.button("发送", type="primary"):
    if narrator_input:
        st.session_state.chat_history.append({
            "role": "narrator",
            "name": "旁白",
            "content": narrator_input
        })
        trigger_autosave()
        st.rerun()

# ================== 核心调度逻辑 ==================
if st.session_state.status == "RUNNING":
    # 获取管理器实例
    context_mgr = get_context_manager()
    memory_mgr = get_memory_manager()
    flow_ctrl = get_flow_controller()
    
    # 流控制：动态延迟
    flow_ctrl.wait()
    
    if st.session_state.round_count >= st.session_state.max_rounds:
        st.session_state.status = "PAUSED"
        st.warning(f"已达到最大轮次限制 ({st.session_state.max_rounds})")
        st.rerun()
    
    # 确定当前发言角色
    current_role_idx = st.session_state.turn_index % len(st.session_state.roles)
    role = st.session_state.roles[current_role_idx]
    
    # 获取其他角色列表（用于构建上下文）
    other_roles = [r for r in st.session_state.roles if r['name'] != role['name']]
    
    # 智能构建上下文（基于 token 限制）
    context_history, was_truncated = context_mgr.build_context(
        chat_history=st.session_state.chat_history,
        model_name=role.get('model', 'default'),
        system_prompt_tokens=2000  # 预估系统提示词占用
    )
    
    # 构建增强版系统提示词
    system_prompt = memory_mgr.build_enhanced_system_prompt(
        role=role,
        other_roles=other_roles,
        chat_history=st.session_state.chat_history,
        context_truncated=was_truncated
    )
    
    # 设置当前角色名（用于消息格式化时区分自己和他人）
    role["interface"].set_current_role(role['name'])
    
    # 显示思考状态
    with chat_container:
        truncation_hint = " (上下文已压缩)" if was_truncated else ""
        st.markdown(f"""
        <div style="color: {role['color']}; font-style: italic; padding: 8px;">
            ⏳ {role['name']} 正在思考...{truncation_hint}
        </div>
        """, unsafe_allow_html=True)
    
    # 调用模型
    try:
        reply = role["interface"].chat(system_prompt, context_history)
        
        # 流控制：成功回调
        flow_ctrl.on_success()
        
        # 更新历史
        st.session_state.chat_history.append({
            "role": "assistant",
            "name": role["name"],
            "content": reply
        })
        
        # 更新状态
        st.session_state.turn_index += 1
        st.session_state.round_count += 1
        
        trigger_autosave()
        st.rerun()
        
    except Exception as e:
        # 流控制：错误回调
        error_msg = str(e).lower()
        is_rate_limit = any(kw in error_msg for kw in ["rate limit", "429", "quota"])
        flow_ctrl.on_error(is_rate_limit=is_rate_limit)
        
        if flow_ctrl.should_pause():
            st.error(f"❌ 连续错误过多，对话已暂停: {e}")
            st.session_state.status = "PAUSED"
            flow_ctrl.reset()
        else:
            st.warning(f"⚠️ {role['name']} 发生错误，将重试: {e}")
            st.rerun()  # 触发重试