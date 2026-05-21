# SmartBackup System v2.0

智能备份与同步系统 —— 由**服务端（管理控制台）**、**Web 前端** 与 **Windows 桌面客户端** 组成的三层备份管理体系。

服务端负责策略管理、客户端监控与存储后端配置；客户端执行备份任务，通过临时凭证直接将加密数据上传到存储后端。

## 特性

- **实时通信**：WebSocket + TLS 长连接，客户端状态实时可见，日志流推送
- **三级策略引擎**：分组树继承 → 标签匹配 → 客户端覆盖，灵活控制每台机器的备份行为
- **端到端加密**：AES-256-GCM 文件级加密，密钥由客户端持有，服务端零知识
- **临时凭证上传**：S3 预签名 URL / SFTP 临时账号，客户端直传存储后端，服务端不中转数据
- **多种存储后端**：本地磁盘、S3 兼容存储、SFTP 三种目标
- **增量备份**：基于 mtime + size + MD5 指纹，仅传输变更文件
- **USB 自动备份**：插入 U 盘后自动触发备份任务
- **压缩传输**：zstd 流式压缩，减少带宽消耗
- **自更新**：按策略（强制 / 任务后 / 空闲时）自动下载升级
- **多租户隔离**：普通用户仅可见所属群组客户端，管理员全量管控

## 系统架构

```
┌─────────────┐       WebSocket + TLS       ┌──────────────┐
│  客户端       │◄───────────────────────────►│   服务端       │
│  (Windows)   │   上报/指令/日志/凭证申请    │  (FastAPI)    │
│  PySide6     │                             │  ┌─────────┐  │
│  备份引擎    │                             │  │ MySQL   │  │
└──────┬───────┘                             │  └─────────┘  │
       │ 直接上传 (临时凭证)                   │  ┌─────────┐  │
       ▼                                     │  │ Nginx   │  │
┌─────────────┐                              │  └────┬────┘  │
│ 存储后端     │                              │       │       │
│ 本地/S3/SFTP │                              │  ┌────▼────┐  │
└─────────────┘                              │  │ Web 前端 │  │
                                             │  │ (Vue 3) │  │
                                             │  └─────────┘  │
                                             └───────────────┘
```

## 技术栈

| 组件 | 技术 |
|------|------|
| **后端** | Python 3.10+, FastAPI, SQLAlchemy (async), Alembic |
| **数据库** | MySQL 8.0 (生产) / SQLite (开发) |
| **前端** | Vue 3 + TypeScript + Vite, Element Plus, Tailwind CSS, ECharts |
| **客户端** | Python 3.10+, PySide6, websocket-client, PyCryptodome, boto3, paramiko |
| **反向代理** | Nginx (静态资源 + API 代理 + WebSocket 升级) |

## 快速开始（Docker Compose）

```bash
# 1. 构建前端
cd web && npm install && npm run build && cd ..

# 2. 启动所有服务 (MySQL + Server + Nginx)
docker compose up -d

# 3. 访问 Web 控制台
# http://localhost

# 4. 首次登录（默认管理员）
# 用户名: admin
# 密码:   admin123
```

## 快速开始（开发模式）

### 1. 服务端

```bash
cd server
pip install -r requirements.txt

# 使用 SQLite（默认，零配置）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 或指定 MySQL 数据库
DATABASE_URL="mysql+aiomysql://user:pass@localhost:3306/backup_db" \
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API 文档自动生成：http://localhost:8000/docs

### 2. Web 前端

```bash
cd web
npm install
npm run dev         # → http://localhost:5173
```

### 3. 桌面客户端

```bash
cd client
pip install -r requirements.txt

# GUI 模式（需要 Windows + PySide6）
python -m client.src.main

# 控制台模式（无 GUI）
python -m client.src.main --console
```

## 环境变量

服务端通过 `.env` 文件或环境变量配置（`server/app/config.py`）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./smart_backup.db` | 数据库连接串 |
| `SECRET_KEY` | (内置占位符) | JWT 签名密钥，生产环境必须修改 |
| `DEBUG` | `true` | 调试模式（允许所有 CORS） |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | 允许的前端跨域源 |
| `WS_HEARTBEAT_INTERVAL` | `30` | WebSocket 心跳间隔（秒） |
| `WS_HEARTBEAT_TIMEOUT` | `90` | 心跳超时，标记离线（秒） |
| `CREDENTIAL_TTL` | `600` | 临时凭证有效期（秒） |
| `MAX_UPLOAD_SIZE` | `524288000` | 上传文件大小限制（500MB） |

## 项目结构

```
system_backup/
├── server/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # REST API 端点（9 个路由器）
│   │   ├── models/         # SQLAlchemy ORM 模型（11 张表）
│   │   ├── schemas/        # Pydantic 请求/响应模型
│   │   ├── services/       # 业务逻辑（认证/策略/凭证/校验）
│   │   ├── middleware/     # JWT 认证中间件
│   │   ├── websocket/      # WebSocket 连接管理与消息路由
│   │   ├── utils/          # 工具函数
│   │   ├── config.py       # 配置管理
│   │   ├── database.py     # 数据库引擎与会话
│   │   └── main.py         # 应用入口
│   ├── alembic/            # 数据库迁移
│   └── requirements.txt
├── web/                    # Vue 3 前端
│   ├── src/
│   │   ├── api/            # Axios API 封装
│   │   ├── views/          # 页面组件（9 个页面）
│   │   ├── components/     # 通用组件
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── router/         # 路由配置
│   │   ├── types/          # TypeScript 类型
│   │   └── utils/          # 工具函数
│   └── package.json
├── client/                 # Windows 桌面客户端
│   ├── src/
│   │   ├── gui/            # PySide6 GUI（主窗口 + 托盘 + 登录）
│   │   ├── engine/         # 备份引擎（扫描/调度/USB监听/任务执行）
│   │   ├── crypto/         # 加密与压缩（AES-256-GCM + zstd）
│   │   ├── upload/         # 上传模块（S3 / SFTP / Local）
│   │   ├── network/        # WebSocket 客户端与消息处理
│   │   ├── storage/        # 本地 SQLite 指纹库
│   │   ├── updater/        # 自更新模块
│   │   └── config.py       # 客户端配置
│   └── requirements.txt
├── docker-compose.yml      # Docker 编排
├── nginx.conf              # Nginx 反向代理配置
└── LICENSE                 # MIT License
```

## API 概览

所有 API 基础路径 `/api/v1`，认证使用 `Authorization: Bearer <JWT>`。

| 模块 | 路径前缀 | 说明 |
|------|---------|------|
| 认证 | `/api/v1/auth/*` | 登录、注册、当前用户 |
| 客户端 | `/api/v1/clients/*` | 列表、详情、分组/标签绑定、指令下发、日志 |
| 分组 | `/api/v1/groups/*` | 树形分组 CRUD |
| 标签 | `/api/v1/tags/*` | 标签 CRUD |
| 策略 | `/api/v1/policies/*` | 模板 CRUD、批量分配、生效策略查询 |
| 存储 | `/api/v1/storages/*` | 存储后端 CRUD |
| 版本 | `/api/v1/versions/*` | 客户端版本管理、文件上传、推送 |
| 备份 | `/api/v1/backups/*` | 备份历史查询 |
| 系统 | `/api/v1/system/*` | 状态、数据库初始化 |
| WebSocket | `/api/v1/ws` | 客户端实时通信 |

完整 API 文档：启动服务端后访问 http://localhost:8000/docs

## WebSocket 通信协议

客户端与服务端通过 WebSocket 交换 JSON 消息。

### 客户端 → 服务端

| type | 说明 |
|------|------|
| `register` | 上报 uuid、IP、系统版本 |
| `heartbeat` | 心跳（30 秒间隔） |
| `log` | 批量推送日志 |
| `auth` | 用户登录绑定 |
| `request_upload_credential` | 申请上传临时凭证 |
| `backup_status` | 备份进度 / 结果上报 |
| `config_ack` | 确认配置更新 |
| `version_check` | 请求版本更新 |

### 服务端 → 客户端

| type | 说明 |
|------|------|
| `welcome` | 连接成功 |
| `auth_result` | 登录结果 |
| `config_update` | 下发配置策略 |
| `upload_credential` | 下发临时凭证 |
| `backup_command` | 主动触发备份 |
| `version_notify` | 版本更新通知 |
| `error` | 错误信息 |

## 安全

- **TLS 传输**：WebSocket over TLS，自签证书 + 客户端公钥固定防中间人
- **JWT 认证**：24 小时有效期，API 中间件校验
- **密码存储**：bcrypt 哈希
- **端到端加密**：AES-256-GCM，DEK + KEK 双层密钥，服务端零知识
- **临时凭证**：S3 预签名 URL 10 分钟有效期，SFTP 临时用户单次使用后销毁
- **多租户隔离**：API 查询自动按用户权限过滤
- **ORM 防护**：SQLAlchemy 参数化查询防止 SQL 注入

## License

MIT © 2026 MiaoJiyu
