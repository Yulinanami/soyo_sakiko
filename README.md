# 🎸 SoyoSaki (素祥同人文聚合阅读器)

SoyoSaki 是一个聚合了 AO3、Pixiv 和 Lofter 平台的同人小说阅读器。用于快速获取长崎素世 (Soyo) 和丰川祥子 (Sakiko) 的 CP同人文。

---

## 功能

- **多源聚合搜索**：同时搜索 AO3、Pixiv 和 Lofter 上的同人文。
- **收藏与历史**：用户注册/登录，收藏夹和阅读历史存于本地数据库。
- **凭证管理**：配置 Pixiv 和 Lofter 的用户凭证，获取同人文内容（AO3 无需凭证）。
- **本地部署**：本地环境部署，无需服务器。

---

## 技术栈

### 前端
- **Framework**: Vue 3 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS v4 (Previous config adjusted for v4 compat)
- **State Management**: Pinia
- **Router**: Vue Router
- **Icons**: Lucide Vue Next

### 后端
- **Framework**: FastAPI (Python)
- **Database**: SQLite (SQLAlchemy + Alembic)
- **Authentication**: JWT (Login/Register)
- **Crawlers**:
  - `ao3-api` (AO3)
  - `pixivpy3` (Pixiv)
  - `playwright` (Lofter dynamic scraping)
- **Caching**: Redis (Optional but recommended for performance)

---

## 快速开始

### 运行环境
- Node.js (v18+)
- Python (v3.10+)
- Redis

### 克隆项目

```bash
git clone https://github.com/Yulinanami/soyo_sakiko
```

### 1. 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装 Playwright 浏览器内核
playwright install chromium

# 配置环境变量 (Windows)
copy .env.example .env
# 配置环境变量 (Linux/Mac)
cp .env.example .env

# 安装依赖
pip install -r requirements.txt

# 启动后端服务
uvicorn app.main:app --reload
```
后端服务将运行在 `http://localhost:8000`

### 2. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

---

## 开源协议

[MIT License](LICENSE)
