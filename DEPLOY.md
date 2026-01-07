# 部署指南

由于 VersaChat 是一个基于 Streamlit 的 Web 应用，最简单、最快捷的公开部署方式是使用 **Streamlit Cloud**。它是完全免费的，并且与 GitHub 无缝集成。

## 部署步骤

### 1. 准备工作

确保你的代码已推送到 GitHub（你已经完成了这一步！）。
确保仓库中有 `requirements.txt` 文件（项目中已包含）。

### 2. 注册并登录 Streamlit Cloud

1. 访问 [Streamlit Cloud](https://share.streamlit.io/)
2. 点击 "Sign up with GitHub" 或 "Continue with GitHub" 使用你的 GitHub 账号登录。

### 3. 创建应用

1. 登录后，点击右上角的 **"New app"** 按钮。
2. 在 **"App URL"** 页面，如果你授权了 GitHub 访问，它可以自动列出你的仓库。填写以下信息：
   - **Repository**: 选择 `quqio/VersaChat`
   - **Branch**: `main`
   - **Main file path**: `app.py`
3. 点击 **"Deploy!"** 部署。

### 4. 配置 API Key (Secrets)

应用启动后可能会报错，因为云端环境没有配置 API Key。你需要通过 Streamlit 的 Secrets 管理功能添加配置：

1. 在应用页面右下角，点击 **"Manage app"**（或者点击右上角三个点 -> Settings）。
2. 点击 **"Secrets"** 标签页。
3. 在文本框中粘入你的配置，格式如下（参考 `.env.example`，但使用 TOML 格式）：

```toml
# .streamlit/secrets.toml format

# DashScope (如果您使用通义千问)
DASHSCOPE_API_KEY = "sk-..."

# OpenAI (如果您使用 GPT)
OPENAI_API_KEY = "sk-..."
OPENAI_BASE_URL = "https://api.openai.com/v1"

# Anthropic (如果您使用 Claude)
ANTHROPIC_API_KEY = "sk-..."
```

**注意**：Ollama 是本地模型服务，无法直接在 Streamlit Cloud 运行（因为它没有 GPU 也没法运行本地服务）。如果您想在云端使用，建议只配置 DashScope (通义千问) 或 OpenAI。

4. 点击 **"Save"** 保存。应用会自动重新加载，此时应该就可以正常使用了！

## 其他部署方式

### Docker 部署（高级）

如果您有一台云服务器（如阿里云 ECS、腾讯云 CVM），可以使用 Docker 部署。

1. **构建镜像**
   ```bash
   docker build -t versachat .
   ```

2. **运行容器**
   ```bash
   docker run -d -p 8501:8501 --env-file .env versachat
   ```

### Hugging Face Space

您也可以将其部署到 Hugging Face Spaces：
1. 创建一个新的 Space，SDK 选择 **Streamlit**。
2. 将代码推送到 Hugging Face 的 Git 仓库。
3. 在 Space 的 **Settings** -> **Variables and secrets** 中配置 API Key。

---

🎉 部署成功后，你会获得一个 `https://versachat.streamlit.app` (或其他自定义域名) 的链接，可以分享给任何人访问！
