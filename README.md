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

### 数据源支持的排序方式

| 排序方式     | AO3    | Bilibili | Pixiv    | Lofter   |
| :----------- | :----- | :------- | :------- | :------- |
| **最近更新** | ✅ 支持 | ✅ 支持   | ✅ 支持   | ✅ 支持   |
| **最多点赞** | ✅ 支持 | ✅ 支持   | ✅ 支持   | ✅ 支持   |
| **最多阅读** | ✅ 支持 | ✅ 支持   | ❌ 不支持 | ✅ 支持   |
| **字数**     | ✅ 支持 | ❌ 不支持 | ❌ 不支持 | ❌ 不支持 |

> **注意**: Pixiv 的热门排序通常需要会员权限。如果没有会员，可能无法返回准确的热门结果。

---

## 筛选与过滤逻辑详解

| 数据源       | 获取逻辑                                                                          | 过滤逻辑                                                                                     |
| :----------- | :-------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------- |
| **Bilibili** | 提取选中列表的第一个标签发起搜索。                                                | 检查结果是否确实包含选中的任一标签（匹配标签/标题/简介）；并扫描详情页的标签执行黑名单拦截。 |
| **Lofter**   | 提取选中列表的第一个标签发起搜索。                                                | 命中屏蔽词立即丢弃。                                                                         |
| **Pixiv**    | 使用所有选中的标签分别搜一遍，最后将结果去重合并。                                | 在结果合并过程中，对比标题和标签列表进行黑名单剔除。                                         |
| **AO3**      | 使用 `OR` 将标签组合后，分页抓取搜索结果（最多3页），对每个结果执行严格包含检测。 | 检查返回作品的标题、角色关系及所有自由标签是否命中黑名单。                                   |


---

## 注意
1. AO3、Pixiv 数据源需要使用代理才能访问。
2. 除非你已经配置过代理软件的路由，否则不要使用TUN（虚拟网卡），这会导致无法访问本地服务。
3. 对于Bilibili数据源获取的同人文，如果提示“获取失败: -352”可以点击返回列表再重新点击该同人文多试几次，或者可以点击在Bilibili上阅读。
4. 如果lofter无法获取同人文，可以尝试关闭代理软件。

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
- **Database**: SQLite (SQLAlchemy)
- **Authentication**: JWT (Login/Register)
- **Crawlers**:
  - `playwright` (AO3 & Lofter dynamic scraping)
  - `pixivpy3` (Pixiv)
  - `httpx` (Bilibili)

### 运行环境
- Node.js (v18+)
- Python (v3.10+)

---

## 快速开始（推荐）

1. 先运行 setup.bat
2. 然后运行 run.bat

---

## 手动启动项目（无法使用快速开始脚本）

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
