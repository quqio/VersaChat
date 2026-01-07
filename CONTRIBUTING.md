# 贡献指南

感谢你对 VersaChat 的兴趣！我们欢迎各种形式的贡献。

## 如何贡献

### 报告 Bug

如果你发现了 Bug，请创建一个 Issue，包含以下信息：

1. **问题描述** - 清晰描述问题
2. **复现步骤** - 详细的复现步骤
3. **期望行为** - 你期望的正确行为
4. **实际行为** - 实际发生的情况
5. **环境信息** - Python 版本、操作系统等

### 提交功能建议

我们欢迎新功能建议！请在 Issue 中描述：

1. 功能的使用场景
2. 功能的详细描述
3. 可能的实现方案（可选）

### 提交代码

1. **Fork 仓库** - 点击右上角的 Fork 按钮
2. **克隆到本地**
   ```bash
   git clone https://github.com/your-username/VersaChat.git
   cd VersaChat
   ```
3. **创建特性分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **进行修改** - 编写代码，添加测试
5. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加某某功能"
   ```
6. **推送到远程**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **创建 Pull Request** - 在 GitHub 上创建 PR

## 代码规范

### Python 风格

- 遵循 [PEP 8](https://pep8.org/) 风格指南
- 使用类型注解
- 每个函数和类添加文档字符串

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

类型包括：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### 示例

```bash
feat(llm): 添加 Ollama 模型支持
fix(session): 修复会话保存失败的问题
docs(readme): 更新安装说明
```

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/VersaChat.git
cd VersaChat

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行应用
streamlit run app.py
```

## 项目结构

```
VersaChat/
├── app.py                 # 主应用入口
├── llm_backend.py         # LLM 接口层
├── context_manager.py     # 上下文管理
├── config_manager.py      # 配置管理
├── session_manager.py     # 会话管理
├── templates.py           # 模板管理
└── ...
```

## 测试

目前项目尚未包含自动化测试，欢迎贡献测试用例！

## 问题反馈

如有任何问题，请通过以下方式联系：

- 创建 GitHub Issue
- 发送邮件至 [your-email@example.com]

再次感谢你的贡献！🎉
