# -*- coding: utf-8 -*-
"""
VersaChat 会话管理器
负责会话的保存、加载、导出功能
"""

import json
import os
import datetime
import uuid
from typing import List, Dict, Tuple, Any
import streamlit as st
from llm_backend import ModelInterface

SESSION_DIR = "saved_sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)


def generate_session_id() -> str:
    """生成唯一会话 ID"""
    return str(uuid.uuid4())


def list_sessions() -> List[str]:
    """返回所有会话文件名的列表"""
    files = [f for f in os.listdir(SESSION_DIR) if f.endswith(".json")]
    return sorted(files, key=lambda x: os.path.getmtime(os.path.join(SESSION_DIR, x)), reverse=True)


def autosave_session(session_id: str, session_name: str = None) -> bool:
    """
    自动保存当前状态
    
    Args:
        session_id: 会话 ID
        session_name: 会话名称（可选）
    
    Returns:
        是否保存成功
    """
    filepath = os.path.join(SESSION_DIR, f"{session_id}.json")
    
    # 1. 确定名称
    current_name = session_name
    if not current_name:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                    current_name = old_data.get("name", "新场景")
            except:
                current_name = "新场景"
        else:
            current_name = "新场景"

    # 2. 准备数据 - 兼容新旧字段名
    serializable_roles = []
    
    # 优先使用新字段名 'roles'，回退到旧字段名 'agents'
    roles_data = st.session_state.get("roles", st.session_state.get("agents", []))
    
    for role in roles_data:
        role_data = role.copy()
        if 'interface' in role_data:
            del role_data['interface']
        serializable_roles.append(role_data)

    data = {
        "id": session_id,
        "name": current_name,
        "last_modified": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "roles": serializable_roles,  # 新字段名
        "agents": serializable_roles,  # 保持向后兼容
        "chat_history": st.session_state.get("chat_history", []),
        "turn_index": st.session_state.get("turn_index", 0),
        "round_count": st.session_state.get("round_count", 0)
    }

    # 3. 写入文件
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Autosave failed: {e}")
        return False


def load_session(session_id: str) -> Tuple[bool, str]:
    """
    加载指定 ID 的会话
    
    Args:
        session_id: 会话 ID
    
    Returns:
        (是否成功, 消息)
    """
    filepath = os.path.join(SESSION_DIR, f"{session_id}.json")
    if not os.path.exists(filepath):
        return False, "存档文件不存在"
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 恢复状态
        st.session_state.chat_history = data.get("chat_history", [])
        st.session_state.turn_index = data.get("turn_index", 0)
        st.session_state.round_count = data.get("round_count", 0)
        st.session_state.session_id = data.get("id", session_id)
        st.session_state.session_name = data.get("name", "新场景")
        st.session_state.status = "PAUSED"
        
        # 恢复角色 - 兼容新旧字段名
        roles_data = data.get("roles", data.get("agents", []))
        restored_roles = []
        for role_data in roles_data:
            role_data['interface'] = ModelInterface(role_data['type'], role_data['model'])
            restored_roles.append(role_data)
        
        # 设置新字段名
        st.session_state.roles = restored_roles
        # 保持向后兼容
        st.session_state.agents = restored_roles
        
        return True, "加载成功"
    except Exception as e:
        return False, f"加载失败: {str(e)}"


def get_all_sessions() -> List[Dict[str, Any]]:
    """获取所有会话的摘要信息"""
    sessions = []
    files = [f for f in os.listdir(SESSION_DIR) if f.endswith(".json")]
    
    for f in files:
        path = os.path.join(SESSION_DIR, f)
        try:
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                # 兼容新旧字段名
                role_count = len(data.get("roles", data.get("agents", [])))
                sessions.append({
                    "id": data.get("id", f.replace(".json", "")),
                    "name": data.get("name", "Untitled"),
                    "last_modified": data.get("last_modified", ""),
                    "role_count": role_count,
                    "agent_count": role_count  # 向后兼容
                })
        except:
            continue
    
    sessions.sort(key=lambda x: x["last_modified"], reverse=True)
    return sessions


def delete_session(session_id: str) -> bool:
    """删除会话"""
    path = os.path.join(SESSION_DIR, f"{session_id}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


# ================== 导出功能 ==================

def export_session_markdown(session_name: str, roles: List[Dict], 
                            chat_history: List[Dict]) -> str:
    """
    将对话导出为 Markdown 格式
    
    Args:
        session_name: 场景名称
        roles: 角色列表
        chat_history: 对话历史
    
    Returns:
        Markdown 格式的字符串
    """
    lines = []
    
    # 标题
    lines.append(f"# {session_name}")
    lines.append("")
    lines.append(f"*导出时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")
    
    # 角色介绍
    lines.append("## 角色")
    lines.append("")
    for role in roles:
        lines.append(f"### {role['name']}")
        lines.append(f"- **模型**: {role.get('model', 'N/A')}")
        lines.append(f"- **人格设定**: {role.get('persona', 'N/A')[:100]}...")
        lines.append("")
    
    # 对话内容
    lines.append("## 对话记录")
    lines.append("")
    
    for msg in chat_history:
        name = msg.get('name', 'Unknown')
        content = msg.get('content', '')
        role_type = msg.get('role', '')
        
        if role_type == 'narrator':
            lines.append(f"> 💬 **旁白**: {content}")
        else:
            lines.append(f"**{name}**:")
            lines.append("")
            lines.append(content)
        
        lines.append("")
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def export_session_json(session_id: str, session_name: str,
                        roles: List[Dict], chat_history: List[Dict]) -> str:
    """
    将对话导出为 JSON 格式
    
    Args:
        session_id: 会话 ID
        session_name: 场景名称
        roles: 角色列表
        chat_history: 对话历史
    
    Returns:
        JSON 格式的字符串
    """
    # 移除不可序列化的 interface 对象
    serializable_roles = []
    for role in roles:
        role_copy = role.copy()
        if 'interface' in role_copy:
            del role_copy['interface']
        serializable_roles.append(role_copy)
    
    data = {
        "version": "1.0",
        "export_time": datetime.datetime.now().isoformat(),
        "session": {
            "id": session_id,
            "name": session_name
        },
        "roles": serializable_roles,
        "chat_history": chat_history,
        "statistics": {
            "total_messages": len(chat_history),
            "role_count": len(roles),
            "narrator_messages": len([m for m in chat_history if m.get('role') == 'narrator'])
        }
    }
    
    return json.dumps(data, ensure_ascii=False, indent=2)