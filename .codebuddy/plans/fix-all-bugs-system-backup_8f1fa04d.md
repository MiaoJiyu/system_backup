---
name: fix-all-bugs-system-backup
overview: 修复 system_backup 项目中 7 大类 bug：客户端状态更新、客户端配置编辑、分组树管理、策略分配、版本上传下载、用户管理及其他问题。
todos:
  - id: fix-heartbeat-offline
    content: 修复客户端状态离线检测：main.py 注册 heartbeat 后台任务，router.py 断开时更新 DB 状态为 offline
    status: completed
  - id: add-client-config-edit
    content: 实现客户端配置编辑：clients.py 新增 config 推送端点，handler.py 新增 request_config 处理，ClientDetailView 策略标签页改为可编辑表单
    status: completed
  - id: add-group-client-membership
    content: 实现分组树客户端成员管理：groups.py 新增 3 个组内客户端端点，GroupsView 添加成员管理面板
    status: completed
  - id: fix-policy-assignment
    content: 修复策略分配：policies.py 新增 3 个 DELETE 端点，PoliciesView 添加分配 UI，GroupsView 加载 boundPolicies
    status: completed
  - id: add-version-download
    content: 添加版本下载端点：versions.py 新增 GET /download/{version}，VersionsView 添加下载按钮
    status: completed
  - id: fix-user-management
    content: 完善用户管理：auth.py 新增 change-password + users CRUD 共 4 个端点，SystemView 加载用户列表并添加操作按钮
    status: completed
  - id: fix-other-bugs
    content: 修复其他遗漏：system.py 新增 init-db 端点，确认所有 disconnect 路径正确更新 DB 状态
    status: completed
    dependencies:
      - fix-heartbeat-offline
---

## 用户需求

修复智能备份与同步系统 v2.0 中存在的 7 个核心 Bug：

1. **客户端状态显示错误**：客户端 WebSocket 断开后，服务端仍显示在线，没有超时离线检测机制
2. **无法编辑客户端配置**：网页端无法编辑客户端配置文件，缺少远程文件管理和配置编辑功能
3. **分组树无法添加客户端**：分组管理页面只能管理分组属性，无法将客户端加入或移出分组
4. **无法分配策略**：策略管理页面只能编辑策略模板，无法将策略分配给客户端、分组或标签
5. **版本无法下载**：客户端版本上传功能正常，但缺少下载端点，生成的 download_url 指向不存在的路由
6. **用户管理缺失**：无法修改密码，无法查看用户列表，无法编辑或删除用户
7. **其他遗漏**：init-db 端点缺失，WebSocket 断开连接时数据库状态未更新

## 核心功能

- 定时心跳检测 + 超时离线标记，确保客户端状态准确
- 远程配置文件编辑（通过 WebSocket + REST API）
- 分组树内管理客户端成员（添加/移除/查看）
- 策略分配 UI（将策略绑定到客户端、分组、标签）+ 删除分配的 API
- 客户端版本文件下载端点
- 用户密码修改、用户列表、用户编辑/删除
- init-db 端点补齐

## 技术栈

- **后端**：Python 3.10+, FastAPI, SQLAlchemy (async), asyncio
- **前端**：Vue 3 + TypeScript, Element Plus, Tailwind CSS, Axios
- **通信**：WebSocket (JSON 消息), REST API

## 实现方案

### Bug 1 — 客户端状态离线检测

**策略**：在 FastAPI lifespan 中启动 asyncio 后台任务，定期调用已有的 `manager.check_heartbeats()`；在 WebSocket 断开时同步更新数据库状态。

**关键改动**：

1. **`server/app/main.py`**：在 `lifespan` 中注册 `asyncio.create_task(run_heartbeat_checker())`，每 15 秒循环调用 `manager.check_heartbeats()`
2. **`server/app/websocket/router.py`**：在 `try/except WebSocketDisconnect` 的 `except` 块中，断开连接后调用 `manager.disconnect(ws)` 的同时，通过 AsyncSessionLocal 更新 `client.status = ClientStatus.offline`
3. **`server/app/websocket/manager.py`**：在 `disconnect()` 方法中加入数据库写入逻辑

**流程**：

- 正常心跳：客户端每 30s 发送 heartbeat → handler 更新 `last_heartbeat` → 后台任务每 15s 检查，超过 90s 未心跳的标记为 offline
- 断开连接：`router.py` catch WebSocketDisconnect → 更新 DB status=offline → 清理内存连接

### Bug 2 — 客户端配置文件编辑

**策略**：新增 WebSocket 消息类型 `request_config` / `config_update`（已有 config_update），并在 client API 中添加重推配置的 REST 端点，前端在 ClientDetailView 中添加策略编辑表单，保存后通过 REST → WebSocket 推送到客户端。

**关键改动**：

1. **`server/app/api/clients.py`**：新增 `PATCH /clients/{id}/config` 接受自定义策略 JSON，保存到 `ClientPolicyOverride.override_config`，然后通过 WebSocket 推送 `config_update`
2. **`server/app/websocket/handler.py`**：新增 `request_config` 消息处理——客户端请求最新配置时重新推送
3. **`web/src/views/ClientDetailView.vue`**：将"生效策略"标签页从只读 JSON 改为可编辑表单，添加"保存并推送"按钮

### Bug 3 — 分组树添加客户端

**策略**：在 groups API 中添加管理组内客户端的端点，前端 GroupsView 在选中分组时显示成员列表和添加/移除控件。

**关键改动**：

1. **`server/app/api/groups.py`**：新增三个端点：

- `GET /groups/{id}/clients` — 返回该分组下的所有客户端列表
- `POST /groups/{id}/clients` — 接受 `client_ids: list[int]`，批量设置客户端的 `group_id`
- `DELETE /groups/{id}/clients/{client_id}` — 将指定客户端移出分组（设 `group_id=None`）

2. **`web/src/api/groups.ts`**：新增 `getGroupClients(id)`, `addClientsToGroup(id, clientIds)`, `removeClientFromGroup(id, clientId)`
3. **`web/src/views/GroupsView.vue`**：在右侧面板中新增"组内客户端"模块——显示客户端列表，支持添加/移除操作。添加使用 `el-transfer` 穿梭框选择客户端。

### Bug 4 — 策略分配

**策略**：补齐后端 DELETE 端点，前端 PoliciesView 增加策略分配 UI，GroupsView 中的 boundPolicies 从 API 加载真实数据。

**关键改动**：

1. **`server/app/api/policies.py`**：新增两个端点：

- `DELETE /assignments/group/{assignment_id}` — 删除 GroupPolicy 记录
- `DELETE /assignments/tag/{assignment_id}` — 删除 TagPolicy 记录
- `DELETE /assignments/client/{assignment_id}` — 删除 ClientPolicyOverride 记录
（URL 格式对齐前端 `removeAssignment(type, id)` 调用）

2. **`web/src/views/PoliciesView.vue`**：在选中策略模板时，右侧面板底部新增"分配到此策略"区域——可选择分配类型（客户端/分组/标签），通过 `el-select` 选中目标，调用 `assignPolicy()`
3. **`web/src/views/GroupsView.vue`**：在 `onMounted` 中调用 `getAssignments()` API 获取该分组的绑定策略并填充 `boundPolicies`

### Bug 5 — 版本下载

**策略**：在 versions.py 中添加 `GET /download/{version}` 路由，返回文件流。

**关键改动**：

1. **`server/app/api/versions.py`**：新增：

```python
@router.get("/download/{version}")
async def download_version(version: str, ...):
# 查询 ClientVersion 记录 → 构建文件路径 → 返回 FileResponse
```

使用 `FileResponse` 流式返回文件，支持 HTTP Range 请求

2. **`web/src/views/VersionsView.vue`**：在操作列添加"下载"按钮，点击后直接触发浏览器下载

### Bug 6 — 用户管理

**策略**：在 auth.py 中补齐用户管理全套端点，前端 SystemView 加载用户列表并添加操作按钮。

**关键改动**：

1. **`server/app/schemas/auth.py`**：新增 `ChangePasswordRequest(BaseModel)` 和 `UserUpdate(BaseModel)` Schema
2. **`server/app/api/auth.py`**：新增四个端点：

- `POST /auth/change-password`：接受 `{old_password, new_password}`，校验旧密码后更新
- `GET /users`：返回所有用户列表（仅管理员）
- `DELETE /users/{id}`：删除指定用户（仅管理员，不能删除自己）
- `PUT /users/{id}`：更新用户名或角色（仅管理员）

3. **`web/src/api/auth.ts`**：新增 `changePassword()`, `getUsers()`, `deleteUser(id)`, `updateUser(id, data)`
4. **`web/src/views/SystemView.vue`**：在 `onMounted` 中 fetch 用户数据并填充 `users`；表格添加"编辑角色"/"重置密码"/"删除"操作列；添加"修改密码"对话框

### Bug 7 — 其他遗漏

**策略**：补齐 init-db 端点，修复 WebSocket 断开时 DB 状态更新。

**关键改动**：

1. **`server/app/api/system.py`**：新增 `POST /init-db` 端点，调用 `init_db()` 和 `ensure_admin_exists()`
2. **已在 Bug 1 中修复**：`server/app/websocket/router.py` 中 disconnect 时更新 DB 状态
3. **`web/src/api/system.ts`**：`initDatabase()` 已存在，无需修改

## 架构设计

```
main.py (lifespan)
  ├─ background_task: run_heartbeat_checker()  ← 每15s调用manager.check_heartbeats()
  │
  └─ routers
      ├─ /api/v1/auth/*        ← 新增 change-password, /users CRUD
      ├─ /api/v1/groups/{id}/clients  ← 新增组内客户端管理
      ├─ /api/v1/policies/assignments/{type}/{id}  ← 新增DELETE
      ├─ /api/v1/versions/download/{version}       ← 新增GET
      ├─ /api/v1/system/init-db                    ← 新增POST
      ├─ /api/v1/clients/{id}/config               ← 新增PATCH (推配置)
      └─ /api/v1/ws  ← 断开时更新DB status
```

## 目录结构（仅列出修改/新增）

```
server/app/
├── main.py                              # [MODIFY] 注册 heartbeat 后台任务
├── websocket/
│   ├── manager.py                       # [MODIFY] disconnect() 写入 DB status
│   ├── router.py                        # [MODIFY] disconnect 时更新 DB
│   └── handler.py                       # [MODIFY] 新增 request_config 处理
├── api/
│   ├── auth.py                          # [MODIFY] 新增 change-password + /users CRUD (4端点)
│   ├── groups.py                        # [MODIFY] 新增组内客户端管理 (3端点)
│   ├── policies.py                      # [MODIFY] 新增 DELETE assignment (3端点)
│   ├── versions.py                      # [MODIFY] 新增 download 端点 (1端点)
│   ├── system.py                        # [MODIFY] 新增 init-db 端点 (1端点)
│   └── clients.py                       # [MODIFY] 新增 config 推送端点 (1端点)
└── schemas/
    └── auth.py                          # [MODIFY] 新增 ChangePasswordRequest, UserUpdate

web/src/
├── views/
│   ├── GroupsView.vue                   # [MODIFY] 客户端成员管理面板 + boundPolicies
│   ├── PoliciesView.vue                 # [MODIFY] 策略分配 UI
│   ├── SystemView.vue                   # [MODIFY] 用户列表加载 + 操作按钮
│   ├── ClientDetailView.vue             # [MODIFY] 配置编辑标签页
│   └── VersionsView.vue                 # [MODIFY] 下载按钮
├── api/
│   ├── groups.ts                        # [MODIFY] 新增组管理客户端 API
│   └── auth.ts                          # [MODIFY] 新增用户管理 API
```