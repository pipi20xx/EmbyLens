# 🚀 EmbyLens

**EmbyLens** 是一款专为 Emby 设计的工业级媒体库管理与运维调试工具。它基于 **FastAPI + Vue 3 + Naive UI** 构建，旨在通过极致的信息密度和现代化的交互设计，解决 Emby 元数据维护、演员同步、标签映射及 Webhook 审计等核心痛点。

---

## ✨ 核心特性 (Features)

### 🎨 极致的工业美学
- **霓虹紫/现代黑双主题**：深度定制的 Naive UI 皮肤，提供沉浸式的深色操作环境。
- **动态无感切换**：采用组件化渲染架构，功能切换如丝般顺滑，无页面刷新感。
- **收缩侧边栏**：支持平滑收缩，在极简模式下通过图标精准识别功能。

### 🛠️ 原子化调试工具箱 (Toolkit)
- **类型/标签管理**：1:1 复刻原版映射算法，支持 Genre 与 GenreItems 的深度物理同步。
- **元数据锁定器**：精准区分“字段级锁定”与“项目全局主锁”，支持全库批量处理。
- **深度 ID 检索**：输入 TMDB ID 即可瞬间递归解析出剧集、季、集的完整元数据树。
- **单集反向溯源**：通过单集 ID 自动上溯，秒级定位所属剧集及其 TMDB 标识。
- **项目元数据审计**：内置 JSON 探针，在任何层级均可一键调出 Emby 原始 JSON 载荷。

### 📡 实时审计与监控
- **全链路性能审计**：记录每一个 API 请求的耗时、状态及客户端来源。
- **工业级日志 Console**：基于 WebSocket 的实时日志流，支持虚拟滚动、历史回溯、暂停及原始文本导出。
- **Webhook 情报中心**：实时捕获并持久化存储 Emby 的通知事件，支持带后缀的贪婪路由匹配。

### ⚙️ 统一集成中心
- 一站式配置 Emby IP、管理级 API Key、UserID 以及 TMDB API Key。
- 所有的配置均支持本地 SQLite 持久化与前端实时 JSON 调试快照。

---

## 🏗️ 技术栈 (Tech Stack)

- **Frontend**: Vue 3, Vite, Naive UI, Pinia, Material Design Icons.
- **Backend**: FastAPI (Python 3.10+), SQLAlchemy 2.0 (Async), Uvicorn.
- **Database**: SQLite (via aiosqlite).
- **DevOps**: Docker, Docker Compose (Multi-stage build).

---

## 🚀 快速启动 (Quick Start)

通过 Docker 一键部署：

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/EmbyLens.git
cd EmbyLens

# 2. 启动服务
docker-compose up -d --build
```

- **访问地址**: `http://localhost:6565`
- **默认端口**: `6565`
- **数据持久化**: 挂载在本地 `./data` 目录。

---

## 📋 架构宪法 (Architecture Standards)

项目遵循严格的解耦规约，确保高度的可维护性：
- **Layer 1: Core**: 纯算法逻辑，不含 IO 操作。
- **Layer 2: Data**: SQLAlchemy 领域模型，按功能拆分。
- **Layer 3: API & Services**: 物理隔离的原子化端点，每一行控制代码皆可审计。

---

## 🤝 鸣谢 (Credits)
- UI 交互灵感来源于 **Anime-Manager**。
- 核心原子工具逻辑移植自 **Emby-Box**。

## 📄 许可证 (License)
本项目准备公开，请遵循相应开源协议。
