# Human.online - 数字分身平台

> **MindWeave · 思维编织 · 意识镜像**

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

![image-20260409223849636](https://cdn.jsdelivr.net/gh/JoshuaChou2018/oss@main/uPic/UoizfQ.image-20260409223849636.png)

![image-20260409223959879](https://cdn.jsdelivr.net/gh/JoshuaChou2018/oss@main/uPic/VgwAjR.image-20260409223959879.png)



https://github.com/user-attachments/assets/7f6de536-271a-4fa1-b179-7afa34c03354


## 🌐 在线演示

**体验地址：https://humind.life**

无需安装，立即体验数字分身构建和社会模拟！

---

## 📖 项目简介

Human.online 是一个基于 **MindWeave（思维编织）** 理论的数字分身平台：

- **🧠 思维编织** - 上传聊天记录，AI 提取六维思维线索，构建你的数字分身
- **💬 分身对话** - 与自己或名人分身深度对话
- **🌐 社会模拟** - 在沙盒中测试假设事件，观察舆论传播
- **🎭 分身市场** - 探索社区创建的名人分身

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/JoshuaChou2018/human.online.git
cd human.online
```

### 2. 配置 API Key

```bash
# 复制环境变量模板
cp apps/api/.env.example apps/api/.env

# 编辑 .env 文件，添加 LLM API Key
vim apps/api/.env
```

**必需配置（至少选一个）：**

```env
# OpenAI
OPENAI_API_KEY=sk-your-openai-key

# 或 Kimi（中文优化）
KIMI_API_KEY=your-kimi-key

# 或 DeepSeek（推荐）
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEFAULT_LLM_PROVIDER=deepseek
```

获取 API Key：
- [OpenAI](https://platform.openai.com/api-keys)
- [Kimi](https://platform.moonshot.cn/)
- [DeepSeek](https://platform.deepseek.com/)

### 3. 配置环境

```bash
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh
```

### 4. 启动服务

```bash
bash start-local.sh
```

访问：
- **前端**: http://localhost:3000
- **API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

---

## 🏗️ 系统架构

```
Frontend (Next.js 14)  ←→  FastAPI  ←→  PostgreSQL/MongoDB/Redis
      │                         │
      └──────────┬──────────────┘
                 ▼
         OpenAI / Kimi / DeepSeek
```

---

## 🧠 MindWeave 六维理论

| 维度 | 说明 | 来源 |
|------|------|------|
| 思维内核 | 核心认知模式 | 深度文章 |
| 表达风格 | 语言习惯 | 聊天记录 |
| 决策逻辑 | 判断偏好 | 案例分析 |
| 知识图谱 | 认知边界 | 专业书籍 |
| 价值体系 | 价值观 | 公开表态 |
| 情感模式 | 情绪表达 | 聊天访谈 |

---

## 📂 项目结构

```
human.online/
├── apps/
│   ├── web/           # Next.js 前端
│   └── api/           # FastAPI 后端
├── docker-compose.yml
└── start-local.sh     # 一键启动脚本
```

---

## 🔒 伦理声明

- ✅ 用于个人自我探索、教育、文化保存
- ❌ 禁止未经授权创建他人分身
- ❌ 禁止用于欺诈或冒充

---

## 📄 许可证

MIT License © 2024 Human.online

## 📮 联系

- **GitHub**: https://github.com/JoshuaChou2018/human.online
- **演示**: https://humind.life
- **Email:** juexiao.zhou@gmail.com
