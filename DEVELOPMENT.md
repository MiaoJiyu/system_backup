# 开发指南

本文档面向 SmartBackup System v2.0 的开发者和贡献者，涵盖本地开发环境搭建、项目结构详解、编码规范、调试技巧及部署流程。

---

## 目录

- [环境要求](#环境要求)
- [本地开发环境搭建](#本地开发环境搭建)
  - [1. 服务端 (FastAPI)](#1-服务端-fastapi)
  - [2. Web 前端 (Vue 3)](#2-web-前端-vue-3)
  - [3. 桌面客户端 (PySide6)](#3-桌面客户端-pyside6)
- [项目结构详解](#项目结构详解)
- [数据库](#数据库)
  - [表关系](#表关系)
  - [迁移脚本](#迁移脚本)
- [API 开发规范](#api-开发规范)
- [WebSocket 协议](#websocket-协议)
- [策略引擎](#策略引擎)
- [客户端开发](#客户端开发)
  - [打包为 EXE](#打包为-exe)
- [前端开发](#前端开发)
- [调试](#调试)
- [部署](#部署)
- [编码规范](#编码规范)

---

## 环境要求

| 工具 | 最低版本 | 说明 |
|------|---------|------|
| Python | 3.10+ | 服务端与客户端运行环境 |
| Node.js | 18+ | 前端构建 |
| npm | 9+ | 前端依赖管理 |
| MySQL | 8.0 | 生产数据库（开发可用内置 SQLite） |
| Docker | 24+ | 容器化部署（可选） |

**推荐 IDE**：VS Code（安装 Python、Vue、Tailwind CSS 插件）

---

## 本地开发环境搭建

### 1. 服务端 (FastAPI)

```bash
cd server

# 创建虚拟环境
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

# 安装依赖
pip install -r requirements.txt

# 默认使用 SQLite 启动（零配置）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 使用 MySQL 启动
DATABASE_URL="mysql+aiomysql://user:pass@localhost:3306/backup_db" \
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**关键文件说明：**

| 文件 | 作用 |
|------|------|
| `app/config.py` | Pydantic Settings，从 `.env` 或环境变量读取配置 |
| `app/database.py` | Async SQLAlchemy 引擎 + 会话工厂 |
| `app/main.py` | FastAPI 应用入口，注册路由、中间件、WebSocket、lifespan |
| `app/middleware/auth.py` | JWT Bearer Token 校验中间件 |
| `alembic/` | 数据库迁移脚本目录 |

**环境变量**：复制 `server/.env.example` 为 `server/.env` 并修改。

### 2. Web 前端 (Vue 3)

```bash
cd web

npm install

# 开发模式（热重载，默认 http://localhost:5173）
npm run dev

# 类型检查
npx vue-tsc --noEmit

# 生产构建
npm run build          # 输出到 web/dist/
```

**关键文件说明：**

| 文件 | 作用 |
|------|------|
| `src/api/request.ts` | Axios 实例，统一拦截器处理 token、错误 |
| `src/router/index.ts` | Vue Router 路由配置 |
| `src/stores/auth.ts` | 认证状态（token、用户信息） |
| `src/stores/app.ts` | 全局应用状态 |
| `src/stores/clients.ts` | 客户端列表状态管理 |
| `src/stores/websocket.ts` | WebSocket 连接状态管理 |
| `vite.config.ts` | Vite 配置（代理、构建选项） |
| `tailwind.config.js` | Tailwind CSS 配置 |

**Vite 代理**：开发时 API 请求通过 Vite proxy 转发到后端 `http://localhost:8000`。

### 3. 桌面客户端 (PySide6)

> 客户端面向 Windows 平台，PySide6 依赖在 Linux 下也可安装用于测试核心逻辑。

```bash
cd client

# 安装依赖
pip install -r requirements.txt

# 控制台模式（无需 GUI）
python -m client.src.main --console

# GUI 模式（需要图形环境）
python -m client.src.main
```

**客户端入口流程：**

1. 生成/读取 `client.uuid` 作为唯一标识
2. 初始化 `KeyManager`（加密密钥管理）
3. 建立 WebSocket 连接，发送 `register` 消息
4. 接收服务端下发的 `config_update` 配置策略
5. 启动 `BackupScheduler`（定时调度）、`USBMonitor`（U 盘监听）
6. GUI 模式下启动 `MainWindow` + `TrayIcon`

---

## 项目结构详解

```
system_backup/
├── server/                          # FastAPI 服务端
│   ├── app/
│   │   ├── api/                     # REST API 路由器 (9个)
│   │   │   ├── auth.py              # POST /auth/login, /auth/register
│   │   │   ├── clients.py           # GET/PATCH/DELETE /clients/*
│   │   │   ├── groups.py            # CRUD /groups/*
│   │   │   ├── tags.py              # CRUD /tags/*
│   │   │   ├── policies.py          # CRUD /policies/*, 策略分配
│   │   │   ├── storages.py          # CRUD /storages/*
│   │   │   ├── versions.py          # CRUD /versions/*, 文件上传
│   │   │   ├── backups.py           # GET /backups/*
│   │   │   └── system.py            # GET /system/status
│   │   ├── models/                  # SQLAlchemy ORM (11张表)
│   │   │   ├── user.py, client.py, group.py, tag.py
│   │   │   ├── policy_template.py, policy_assignment.py
│   │   │   ├── storage.py, backup_record.py
│   │   │   ├── client_log.py, client_version.py
│   │   ├── schemas/                 # Pydantic 请求/响应 Schema
│   │   ├── services/                # 业务逻辑层
│   │   │   ├── auth_service.py      # 用户认证、JWT、管理员创建
│   │   │   ├── policy_engine.py     # 策略合并引擎
│   │   │   ├── credential_service.py # 临时凭证生成
│   │   │   └── storage_validator.py # 存储配置校验
│   │   ├── websocket/               # WebSocket 处理
│   │   │   ├── manager.py           # ConnectionManager 连接池
│   │   │   ├── handler.py           # 消息路由分发
│   │   │   └── router.py            # WS 端点定义
│   │   ├── middleware/
│   │   │   └── auth.py              # JWT 依赖注入 + 多租户过滤
│   │   ├── utils/
│   │   │   ├── pagination.py        # 分页辅助
│   │   │   └── security.py          # 密码哈希工具
│   │   ├── config.py                # Pydantic Settings 配置
│   │   ├── database.py              # Async Engine + Session
│   │   └── main.py                  # FastAPI 应用入口
│   ├── alembic/                     # 数据库迁移
│   │   ├── env.py                   # Alembic 环境配置
│   │   └── versions/                # 迁移脚本
│   ├── alembic.ini                  # Alembic 配置
│   ├── Dockerfile                   # 服务端容器镜像
│   └── requirements.txt
│
├── web/                             # Vue 3 前端
│   ├── src/
│   │   ├── api/                     # Axios API 封装 (9个)
│   │   │   └── request.ts           # Axios 实例 + 拦截器
│   │   ├── views/                   # 页面组件 (9个)
│   │   │   ├── LoginView.vue, DashboardView.vue
│   │   │   ├── ClientsView.vue, ClientDetailView.vue
│   │   │   ├── GroupsView.vue, PoliciesView.vue
│   │   │   ├── StoragesView.vue, VersionsView.vue
│   │   │   └── SystemView.vue
│   │   ├── components/              # 通用组件
│   │   │   ├── AppLayout.vue        # 主布局（侧边栏 + 顶栏）
│   │   │   └── ConfirmDialog.vue    # 确认对话框
│   │   ├── stores/                  # Pinia 状态管理 (4个)
│   │   │   ├── auth.ts              # 认证状态
│   │   │   ├── app.ts               # 全局状态
│   │   │   ├── clients.ts           # 客户端状态
│   │   │   └── websocket.ts         # WebSocket 状态
│   │   ├── router/index.ts          # 路由配置
│   │   ├── types/index.ts           # TypeScript 类型定义
│   │   ├── utils/csv.ts             # CSV 导出工具
│   │   ├── App.vue                  # 根组件
│   │   ├── main.ts                  # Vue 入口
│   │   └── style.css                # 全局样式（Tailwind）
│   ├── public/favicon.svg
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── tsconfig.json
│   └── package.json
│
├── client/                          # 桌面客户端
│   ├── src/
│   │   ├── gui/                     # PySide6 界面
│   │   │   ├── main_window.py       # 主窗口
│   │   │   ├── tray_icon.py         # 系统托盘
│   │   │   └── login_dialog.py      # 登录对话框
│   │   ├── engine/                  # 备份引擎
│   │   │   ├── scanner.py           # 目录扫描 + 增量检测
│   │   │   ├── scheduler.py         # 定时调度 (cron/interval/manual)
│   │   │   ├── usb_monitor.py       # U 盘插入检测
│   │   │   └── task_runner.py       # 任务执行编排
│   │   ├── crypto/                  # 加密与压缩
│   │   │   ├── key_manager.py       # 密钥管理 (RSA/DEK)
│   │   │   ├── encryptor.py         # AES-256-GCM 文件加密
│   │   │   └── compressor.py        # zstd 流式压缩
│   │   ├── upload/                  # 上传模块
│   │   │   ├── base.py              # 抽象基类
│   │   │   ├── s3_uploader.py       # S3 (boto3)
│   │   │   ├── sftp_uploader.py     # SFTP (paramiko)
│   │   │   └── local_uploader.py    # 本地磁盘
│   │   ├── network/                 # 网络通信
│   │   │   ├── ws_client.py         # WebSocket 客户端 (自动重连)
│   │   │   └── message_handler.py   # 消息分发处理
│   │   ├── storage/db.py            # SQLite 本地指纹库
│   │   ├── updater/updater.py       # 自更新模块
│   │   ├── config.py                # 客户端配置
│   │   └── main.py                  # 入口
│   └── requirements.txt
│
├── docker-compose.yml               # Docker 编排
├── nginx.conf                       # Nginx 反代配置
└── LICENSE                          # MIT License
```

---

## 数据库

### 表关系

```
users (1) ──── (N) clients
groups (树形，自引用 parent_id)
groups (1) ──── (N) clients
groups (1) ──── (N) group_policies ──── (1) policy_templates
tags (1) ──── (N) tag_policies ──── (1) policy_templates
clients (1) ──── (1) client_policy_overrides ──── (1) policy_templates
policy_templates (1) ──── (1) storages (上传目标)
clients (1) ──── (N) backup_records ──── (1) storages
clients (1) ──── (N) client_logs
client_versions (独立)
```

### 迁移脚本

```bash
cd server

# 删除旧数据库（开发时）
rm -f smart_backup.db

# 生成新迁移（模型变更后）
alembic revision --autogenerate -m "描述变更内容"

# 应用迁移
alembic upgrade head

# 回滚
alembic downgrade -1

# 查看迁移历史
alembic history

# 查看当前版本
alembic current
```

### 默认管理员

应用首次启动时自动创建：
- 用户名：`admin`
- 密码：`admin123`

> **生产环境请立即修改密码。**

---

## API 开发规范

### 新增 API 端点

1. 在 `server/app/schemas/` 定义 Pydantic Schema
2. 在 `server/app/services/` 实现业务逻辑
3. 在 `server/app/api/` 创建路由器并绑定依赖
4. 在 `server/app/main.py` 注册路由器

### 路由器模板

```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import AsyncSessionLocal, get_db
from app.middleware.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/example", tags=["example"])

@router.get("/")
async def list_items(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 自动多租户过滤
    ...
```

### 认证中间件

- `get_current_user`：校验 Bearer Token，返回 User 对象
- `require_admin`：附加管理员权限校验
- 查询默认注入 `user_id` 过滤条件实现多租户隔离

### API 响应格式

```json
// 成功（集合）
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}

// 成功（单条）
{
  "id": 1,
  "name": "...",
  ...
}

// 错误
{
  "detail": "错误描述"
}
```

---

## WebSocket 协议

### 客户端连接流程

```
Client                          Server
  │                               │
  │──── ws://host/api/v1/ws ─────►│  TLS 握手
  │◄──────── welcome ────────────│  {server_version, server_time}
  │──── register ────────────────►│  {uuid, ip, os, version}
  │◄──── config_update ──────────│  下发策略
  │──── config_ack ──────────────►│  确认接收
  │                               │
  │──── heartbeat (每30s) ───────►│
  │◄──── heartbeat_ack ──────────│
```

### 消息格式

```json
{
  "type": "消息类型",
  "request_id": "可选的请求 ID，用于关联响应",
  "payload": {}
}
```

### 连接管理器 API

```python
from app.websocket.manager import ws_manager

# 向指定客户端发送消息
await ws_manager.send_to_client(client_uuid, {"type": "config_update", "payload": {...}})

# 获取在线客户端列表
online = ws_manager.get_online_clients()

# 广播消息
await ws_manager.broadcast({"type": "server_shutdown", "payload": {}})

# 断开客户端
await ws_manager.disconnect_client(client_uuid)
```

---

## 策略引擎

策略合并采用三级优先级，从低到高：

```
分组树继承（递归父级）→ 标签匹配（按 priority 排序）→ 客户端覆盖（override_config）
```

### 合并规则

- **浅层覆盖**：高优先级字段直接覆盖低优先级同名字段
- JSON 字段（如 `backup_directories`）整体替换，不做深度合并
- 未指定的字段保留继承值

### 查询最终策略

```python
from app.services.policy_engine import get_effective_policy

policy = await get_effective_policy(db, client_id)
```

### 临时凭证生成

```python
from app.services.credential_service import generate_credential

credential = await generate_credential(
    db, storage_id=1, client_id=5,
    target_path="/backups/client5/2024-01-01/",
    file_size=1024000
)
# 返回: { "storage_id": 1, "type": "s3", "credential": {...}, "expires_in": 600 }
```

---

## 客户端开发

### 模块交互流程

```
main.py
  ├─► WSClient ─► 服务端 WebSocket
  │     └─► MessageHandler ─► 策略更新/版本通知/备份指令 回调
  ├─► BackupScheduler ─► 按 cron/interval 触发 TaskRunner
  ├─► USBMonitor ─► U 盘插入时触发 TaskRunner
  └─► TaskRunner.run()
        ├─► Scanner.scan_directory()         # 扫描变更文件
        ├─► Encryptor.encrypt_file()         # AES-256-GCM 加密
        ├─► Compressor.compress()            # zstd 压缩
        ├─► WSClient.request_credential()    # 申请临时凭证
        └─► Uploader.upload()                # 上传到存储后端
```

### 添加新存储后端

1. 在 `client/src/upload/` 创建新上传器，继承 `BaseUploader`
2. 在 `server/app/services/credential_service.py` 添加对应凭证生成逻辑
3. 在 `server/app/models/storage.py` 的 `type` 枚举中添加新值

### 打包为 EXE

```bash
pip install pyinstaller

# 单文件打包
pyinstaller --onefile --windowed \
  --name SmartBackup \
  --add-data "resources:resources" \
  --hidden-import PySide6 \
  client/src/main.py

# 输出在 dist/SmartBackup.exe
```

---

## 前端开发

### 新增页面

1. 在 `web/src/views/` 创建 `.vue` 文件
2. 在 `web/src/api/` 创建对应的 API 封装
3. 在 `web/src/router/index.ts` 注册路由
4. 在 `web/src/stores/` 添加必要状态（可选）

### 页面模板

```vue
<template>
  <div class="p-6">
    <h1 class="text-2xl font-semibold mb-4">页面标题</h1>
    <!-- Element Plus 组件 -->
    <el-table :data="items" ... />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { exampleApi } from '@/api/example'

const items = ref([])

onMounted(async () => {
  items.value = await exampleApi.list()
})
</script>
```

### 样式规范

- 使用 **Tailwind CSS** 工具类为主
- 定制样式使用 `<style scoped>`
- Element Plus 组件通过 `el-*` 前缀使用

### WebSocket 实时更新

```typescript
import { useWebSocketStore } from '@/stores/websocket'

const wsStore = useWebSocketStore()

// 监听客户端实时日志
wsStore.on('log', (data) => {
  console.log('New log:', data)
})

// 监听客户端状态变化
wsStore.on('status_change', (data) => {
  // 更新客户端列表
})
```

---

## 调试

### 服务端

```bash
# --reload 自动重载代码
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

# 查看所有路由
curl http://localhost:8000/openapi.json | python -m json.tool
```

### 前端

```bash
# 开发模式 + 热重载
npm run dev

# 浏览器 Vue DevTools
# 安装浏览器扩展: Vue.js devtools

# 网络请求调试：浏览器 DevTools → Network 面板
```

### 客户端

```bash
# 启用 DEBUG 日志
python -m client.src.main --console

# 或在代码中
import logging
logging.getLogger("SmartBackup").setLevel(logging.DEBUG)
```

### WebSocket 调试

```bash
# 使用 websocat 测试
websocat wss://localhost/api/v1/ws --insecure
# 或
wscat -c ws://localhost:8000/api/v1/ws
```

---

## 部署

### Docker Compose（推荐）

```bash
# 1. 构建前端
cd web && npm install && npm run build && cd ..

# 2. 启动
docker compose up -d

# 3. 查看日志
docker compose logs -f server
docker compose logs -f nginx

# 4. 停止
docker compose down -v
```

### 手动部署

```bash
# 服务端
cd server
pip install -r requirements.txt
DATABASE_URL="mysql+aiomysql://..." \
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 前端（Nginx 托管静态文件）
cd web && npm install && npm run build
cp -r dist/* /var/www/html/

# 客户端
# 将打包好的 EXE 或源码分发给用户
```

### Nginx 配置要点

- `/` → Vue 构建产物静态文件
- `/api/` → 代理到 `server:8000`
- `/api/v1/ws` → WebSocket 升级代理（需设置 `Upgrade` 和 `Connection` 头）

---

## 编码规范

### Python

- 遵循 **PEP 8** 代码风格
- 使用 **Type Hints** 标注函数参数和返回值
- 异步操作统一使用 `async/await`
- 字符串使用双引号 `"`
- 日志使用 `logging.getLogger(__name__)`

### TypeScript / Vue

- 使用 **Composition API** (`<script setup lang="ts">`)
- 类型定义集中在 `web/src/types/index.ts`
- API 调用统一通过 `web/src/api/` 模块
- 状态管理使用 Pinia
- 页面路由使用懒加载 `() => import(...)`

### Git 提交规范

```
<type>(<scope>): <subject>

type: feat / fix / docs / style / refactor / test / chore
scope: server / web / client / docs / deps
```

示例：
```
feat(server): add backup command endpoint
fix(web): correct pagination offset calculation
docs(client): update encryption setup guide
```

---

## 常见问题

### Q: 如何切换数据库？

修改 `DATABASE_URL` 环境变量：
- SQLite：`sqlite+aiosqlite:///./smart_backup.db`（开发默认）
- MySQL：`mysql+aiomysql://user:pass@host:3306/dbname`

### Q: 前端 API 请求 401 错误？

Token 已过期，重新登录获取新 Token。Token 有效期默认 24 小时（通过 `ACCESS_TOKEN_EXPIRE_MINUTES` 配置）。

### Q: 客户端连接失败？

1. 确认服务端地址和端口正确
2. 检查防火墙设置
3. 查看客户端日志中的 `ws_client` 级别日志
4. 客户端生成 `client.uuid` 文件确认 UUID 正常

### Q: WebSocket 频繁断开重连？

- 检查心跳间隔配置（默认 30s）
- 服务端 `WS_HEARTBEAT_TIMEOUT` 是否过短（默认 90s）
- 检查网络稳定性

---

## 相关资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Vue 3 文档](https://vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [PySide6 文档](https://doc.qt.io/qtforpython-6/)
