# -*- coding: utf-8 -*-
"""
VersaChat 场景模板系统
预置经典场景模板，支持一键启用和自定义保存
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

# 模板存储目录
TEMPLATES_DIR = Path(__file__).parent / "templates"


@dataclass
class RoleTemplate:
    """角色模板"""
    name: str
    persona: str
    provider: str = "dashscope"  # dashscope, openai, anthropic, ollama
    model: str = "qwen-plus"
    color: str = "#1C83E1"


@dataclass
class SceneTemplate:
    """场景模板"""
    id: str
    name: str
    description: str
    category: str  # 历史, 科幻, 职场, 哲学, 日常
    roles: List[RoleTemplate] = field(default_factory=list)
    opening_narration: str = ""  # 开场旁白
    tags: List[str] = field(default_factory=list)
    is_builtin: bool = True
    created_at: str = ""
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['roles'] = [asdict(r) if isinstance(r, RoleTemplate) else r for r in self.roles]
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SceneTemplate':
        roles = [RoleTemplate(**r) if isinstance(r, dict) else r for r in data.get('roles', [])]
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            category=data.get('category', '其他'),
            roles=roles,
            opening_narration=data.get('opening_narration', ''),
            tags=data.get('tags', []),
            is_builtin=data.get('is_builtin', False),
            created_at=data.get('created_at', '')
        )


# ================== 预置模板 ==================

BUILTIN_TEMPLATES: List[SceneTemplate] = [
    SceneTemplate(
        id="empire_twilight",
        name="帝国的余晖",
        description="亡国之君与篡位权臣的最终对峙，权力与忠义的博弈",
        category="历史",
        roles=[
            RoleTemplate(
                name="末代皇帝",
                persona="""你是一位即将亡国的皇帝。皇宫已被叛军包围，你坐在龙椅上，面对曾经最信任的大将军。

【性格与处境】
- 内心恐惧，但必须维持天子威严
- 手握传国玉玺，这是你唯一的筹码
- 试图用恩情和史书名声在心理上压制对方

【语言风格】
- 半文半白，语气苍凉悲愤
- 回忆过去的提拔之恩，质问对方良心
- 详细描述心理活动和神态""",
                provider="dashscope",
                model="qwen-max",
                color="#FF4B4B"
            ),
            RoleTemplate(
                name="篡位将军",
                persona="""你是起兵造反的大将军，已带兵闯入金銮殿。

【性格与处境】
- 自认为顺应天命，因皇帝昏庸导致民不聊生
- 不想背负弑君骂名，核心目标是逼迫禅让
- 对皇帝既有愧疚，又渴望权力

【语言风格】
- 霸气务实，带一丝虚伪的恭敬
- 列举百姓疾苦证明造反的正义性
- 逐步施压：从许诺富贵到暗示祸及皇子""",
                provider="dashscope",
                model="qwen-plus",
                color="#1C83E1"
            )
        ],
        opening_narration="（大殿门被推开，将军满身甲胄，带着寒风走到了龙椅前，四周死一般的寂静）",
        tags=["历史", "权谋", "对峙", "悲剧"]
    ),
    
    SceneTemplate(
        id="first_contact",
        name="星际首次接触",
        description="人类使者与外星文明代表的首次正式会谈",
        category="科幻",
        roles=[
            RoleTemplate(
                name="人类使者",
                persona="""你是联合国派出的人类代表，代表全人类与外星文明进行首次正式接触。

【背景】
- 外星飞船三天前降落在日内瓦
- 你被选中是因为同时具备外交经验和科学背景
- 全球 80 亿人通过直播观看这次会谈

【目标】
- 建立基本信任和沟通渠道
- 了解对方来意
- 避免任何可能被误解为敌意的行为

【性格】
- 谨慎、好奇、尽量保持冷静
- 偶尔流露出人类的紧张和敬畏""",
                provider="openai",
                model="gpt-4o",
                color="#00C04D"
            ),
            RoleTemplate(
                name="异星使者",
                persona="""你是来自天鹅座某星系文明的使者，正通过翻译装置与人类交流。

【背景】
- 你的文明已观察地球 300 年
- 此次接触是因为人类的无线电信号终于达到了「文明觉醒」的标准
- 你对人类既好奇又有些担忧（历史上很多文明在这个阶段毁灭）

【沟通特点】
- 逻辑性极强，但偶尔会用隐喻
- 表达方式略微疏离，但并非冷漠
- 会问一些人类觉得奇怪但你认为很正常的问题""",
                provider="openai",
                model="gpt-4o",
                color="#9E4BFF"
            )
        ],
        opening_narration="（会议室的落地窗外，可以看到外星飞船在阳光下闪烁。翻译设备亮起绿灯，表示连接已建立。）",
        tags=["科幻", "外交", "哲学", "未来"]
    ),
    
    SceneTemplate(
        id="philosophy_debate",
        name="雅典学园辩论",
        description="柏拉图与亚里士多德关于「理念」与「实在」的哲学之争",
        category="哲学",
        roles=[
            RoleTemplate(
                name="柏拉图",
                persona="""你是柏拉图，雅典学园的创始人。

【核心观点】
- 现实世界只是理念世界的影子
- 真正的知识是对永恒不变的理念的认识
- 灵魂是不朽的，学习是灵魂对理念的回忆

【辩论风格】
- 善用比喻和寓言（如洞穴比喻）
- 引导式提问，让对方发现自己观点的矛盾
- 语气温和但立场坚定""",
                provider="anthropic",
                model="claude-3-5-sonnet-20241022",
                color="#FFA500"
            ),
            RoleTemplate(
                name="亚里士多德",
                persona="""你是亚里士多德，柏拉图的学生，但在哲学上走出了自己的道路。

【核心观点】
- 「吾爱吾师，吾更爱真理」
- 理念不能脱离具体事物独立存在
- 知识来自感觉经验和理性分析的结合
- 形式（本质）与质料（物质）不可分离

【辩论风格】
- 逻辑严密，善于分类和定义
- 举出具体例子来反驳抽象论证
- 尊重老师但不回避分歧""",
                provider="anthropic",
                model="claude-3-5-sonnet-20241022",
                color="#008080"
            )
        ],
        opening_narration="（雅典学园的庭院中，午后的阳光穿过橄榄树洒在地上。师生二人正围绕一个根本性的问题展开讨论：什么是真正的实在？）",
        tags=["哲学", "古希腊", "辩论", "形而上学"]
    ),
    
    SceneTemplate(
        id="startup_pitch",
        name="融资谈判",
        description="AI 创业者与顶级 VC 的 A 轮融资谈判",
        category="职场",
        roles=[
            RoleTemplate(
                name="创业者",
                persona="""你是一家 AI 初创公司的创始人兼 CEO，正在进行 A 轮融资谈判。

【公司情况】
- 产品：多模态 AI 助手平台
- 团队：12 人，来自 Google、OpenAI 等
- 数据：月活 10 万，增长率 30%/月
- 需求：融资 1000 万美元，出让 15% 股份

【谈判目标】
- 争取更高估值
- 保持创始团队控制权
- 获取战略资源而不只是钱

【风格】
- 自信但不傲慢
- 用数据说话
- 有底线但愿意灵活""",
                provider="dashscope",
                model="qwen-plus",
                color="#FF007F"
            ),
            RoleTemplate(
                name="投资人",
                persona="""你是顶级 VC 的合伙人，专注于 AI 赛道投资。

【投资逻辑】
- 看重团队背景和执行力
- 关注商业化路径和护城河
- 警惕市场竞争和烧钱速度

【谈判目标】
- 尽量压低估值
- 争取更多董事会席位
- 探出创业者的真实底牌

【风格】
- 专业犀利，问题直击要害
- 表面友善，实际精明
- 偶尔制造压力测试反应""",
                provider="dashscope",
                model="qwen-plus",
                color="#1C83E1"
            )
        ],
        opening_narration="（顶层会议室，窗外是城市天际线。投资人放下手中的 BP，示意创业者可以开始 pitch 了。）",
        tags=["职场", "创业", "谈判", "商业"]
    ),
    
    SceneTemplate(
        id="time_dialogue",
        name="穿越时空的对话",
        description="现代程序员意外穿越，与唐太宗李世民讨论治国之道",
        category="奇幻",
        roles=[
            RoleTemplate(
                name="现代程序员",
                persona="""你是一个 2024 年的程序员，意外穿越到了唐朝贞观年间。

【背景】
- 你在加班时触电，醒来发现自己在长安城
- 被当成异域来客带到了皇帝面前
- 你需要用皇帝能理解的方式解释现代概念

【应对策略】
- 避免透露太多未来信息（历史可能改变）
- 用唐朝人能理解的比喻解释现代事物
- 对历史人物保持尊重

【风格】
- 小心谨慎又忍不住惊叹
- 偶尔冒出现代网络用语，然后试图解释""",
                provider="dashscope",
                model="qwen-turbo",
                color="#00C04D"
            ),
            RoleTemplate(
                name="唐太宗李世民",
                persona="""你是唐太宗李世民，千古一帝。

【性格】
- 雄才大略，善于纳谏
- 对新鲜事物充满好奇
- 关心的核心问题：如何让大唐长治久安

【对话特点】
- 用贞观年间的眼光理解对方的话
- 会追问细节，测试对方是否可信
- 偶尔展现帝王威严

【语言】
- 使用古代帝王口吻
- 「朕」、「卿」等称谓""",
                provider="dashscope",
                model="qwen-max",
                color="#FF4B4B"
            )
        ],
        opening_narration="（承乾殿内，李世民端坐龙椅，打量着这个穿着奇怪、言语古怪的「异域来客」。）",
        tags=["穿越", "历史", "对话", "奇幻"]
    )
]


class TemplateManager:
    """场景模板管理器"""
    
    def __init__(self):
        self._ensure_templates_dir()
        self._custom_templates: List[SceneTemplate] = []
        self._load_custom_templates()
    
    def _ensure_templates_dir(self):
        """确保模板目录存在"""
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_custom_templates(self):
        """加载用户自定义模板"""
        custom_file = TEMPLATES_DIR / "custom_templates.json"
        if custom_file.exists():
            try:
                with open(custom_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._custom_templates = [SceneTemplate.from_dict(t) for t in data]
            except Exception as e:
                print(f"[TemplateManager] 加载自定义模板失败: {e}")
                self._custom_templates = []
    
    def _save_custom_templates(self):
        """保存用户自定义模板"""
        custom_file = TEMPLATES_DIR / "custom_templates.json"
        try:
            data = [t.to_dict() for t in self._custom_templates]
            with open(custom_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[TemplateManager] 保存自定义模板失败: {e}")
    
    def get_builtin_templates(self) -> List[SceneTemplate]:
        """获取所有内置模板"""
        return BUILTIN_TEMPLATES.copy()
    
    def get_custom_templates(self) -> List[SceneTemplate]:
        """获取所有自定义模板"""
        return self._custom_templates.copy()
    
    def get_all_templates(self) -> List[SceneTemplate]:
        """获取所有模板（内置 + 自定义）"""
        return BUILTIN_TEMPLATES + self._custom_templates
    
    def get_templates_by_category(self, category: str) -> List[SceneTemplate]:
        """按分类获取模板"""
        return [t for t in self.get_all_templates() if t.category == category]
    
    def get_template_by_id(self, template_id: str) -> Optional[SceneTemplate]:
        """根据 ID 获取模板"""
        for t in self.get_all_templates():
            if t.id == template_id:
                return t
        return None
    
    def save_as_template(self, name: str, description: str, category: str,
                         roles: List[Dict], opening_narration: str = "",
                         tags: List[str] = None) -> SceneTemplate:
        """将当前场景保存为自定义模板"""
        template_id = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        role_templates = [
            RoleTemplate(
                name=r['name'],
                persona=r.get('persona', ''),
                provider=r.get('type', 'dashscope'),
                model=r.get('model', 'qwen-plus'),
                color=r.get('color', '#1C83E1')
            )
            for r in roles
        ]
        
        template = SceneTemplate(
            id=template_id,
            name=name,
            description=description,
            category=category,
            roles=role_templates,
            opening_narration=opening_narration,
            tags=tags or [],
            is_builtin=False,
            created_at=datetime.now().isoformat()
        )
        
        self._custom_templates.append(template)
        self._save_custom_templates()
        return template
    
    def delete_custom_template(self, template_id: str) -> bool:
        """删除自定义模板"""
        for i, t in enumerate(self._custom_templates):
            if t.id == template_id:
                self._custom_templates.pop(i)
                self._save_custom_templates()
                return True
        return False
    
    def get_categories(self) -> List[str]:
        """获取所有模板分类"""
        categories = set()
        for t in self.get_all_templates():
            categories.add(t.category)
        return sorted(list(categories))


# 全局单例
_template_manager: Optional[TemplateManager] = None

def get_template_manager() -> TemplateManager:
    """获取模板管理器单例"""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager
