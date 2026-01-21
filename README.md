# 🎸 SoyoSaki (素祥同人文聚合阅读器)

SoyoSaki 是一个聚合了 AO3、Pixiv、Lofter 和 Bilibili 平台的同人小说阅读器。用于快速获取长崎素世 (Soyo) 和丰川祥子 (Sakiko) 的 CP同人文。

---

## 功能

- **多源聚合搜索**：同时搜索 AO3、Pixiv、Lofter 和 Bilibili 上素祥同人文。
- **标签过滤**：支持排除不想看的标签。
- **收藏与历史**：用户注册/登录，收藏夹和阅读历史存于本地数据库。
- **凭证管理**：配置 Pixiv 和 Lofter 的用户凭证，获取同人文内容（AO3 和 Bilibili 源无需凭证）。
- **本地部署**：本地环境部署，安全且无需远程服务器。

---

## 注意
1. AO3、Pixiv 数据源需要使用代理才能访问
2. 除非你已经配置过代理软件的路由，否则不要使用TUN（虚拟网卡），这会导致无法访问本地服务

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
  - `httpx` (Bilibili)

---

## 快速开始

### 运行环境
- Node.js (v18+)
- Python (v3.10+)

### 克隆项目

```bash
git clone https://github.com/Yulinanami/soyo_sakiko
cd soyo_sakiko
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

# 配置环境变量 (Windows)
copy .env.example .env
# 配置环境变量 (Linux/Mac)
cp .env.example .env

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器内核
playwright install chromium

# 启动后端服务
uvicorn app.main:app --reload
```
后端服务运行在 `http://localhost:8000`

### 2. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```
使用浏览器进入 `http://localhost:5173` 即可打开程序

---

## 开源协议

[MIT License](LICENSE)
