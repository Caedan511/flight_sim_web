# 前端 API 对接指南

## 目录

- [基础地址](#基础地址)
- [默认管理员](#默认管理员)
- [通用规则](#通用规则)
- [公共字段](#公共字段)
- [登录认证](#登录认证)
- [用户管理](#用户管理)
- [飞行脚本](#飞行脚本)
- [模型管理](#模型管理)
- [仿真任务](#仿真任务)

## 基础地址

前端请求地址：

```text
http://<后端机器 IP>:8000
```

## 默认管理员

默认联调管理员账号：

```text
username: admin
password: admin123
```

## 通用规则

除文件上传和文件下载接口外，请求和响应主体都是 JSON。

JSON 请求头：

```http
Content-Type: application/json
```

文件上传接口使用：

```http
Content-Type: multipart/form-data
```

需要登录的接口必须携带：

```http
Authorization: Bearer <token>
```

成功响应统一结构：

```json
{
  "success": true,
  "message": "Operation message",
  "data": {}
}
```

错误响应统一结构：

```json
{
  "success": false,
  "message": "Error message",
  "data": null
}
```

常见 HTTP 状态码：

| 状态码 | 含义 |
| --- | --- |
| `400` | 请求参数错误或业务校验失败 |
| `401` | 未登录、token 缺失、token 无效 |
| `403` | 已登录但权限不足，或账号被禁用 |
| `404` | 资源不存在 |
| `409` | 当前状态不允许执行该操作 |

## 公共字段

当前接口使用这些业务标识：

| 资源 | 前端使用字段 | 示例 |
| --- | --- | --- |
| 用户 | `uid` | `U000001` |
| 飞行脚本 | `script_code` | `F000001` |
| 模型版本 | `version` | `v1.0.0` |
| 仿真任务 | `task_code` | `T000001` |
| 仿真产物 | `artifact_code` | `T000001-report-report` |

用户对象示例：

```json
{
  "uid": "U000001",
  "username": "admin",
  "role": "admin",
  "status": "active",
  "last_login_at": "2026-08-05T10:00:00",
  "created_at": "2026-08-05T10:00:00",
  "updated_at": "2026-08-05T10:00:00"
}
```

有效用户角色：

```text
admin
normal
```

有效用户状态：

```text
active
disabled
```

## 登录认证

### 接口列表

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| `POST` | `/api/auth/login` | 无 | 登录并获取 token |
| `POST` | `/api/auth/logout` | 登录用户 | 前端清除登录态 |
| `GET` | `/api/auth/me` | 登录用户 | 获取当前用户 |
| `PATCH` | `/api/users/me/password` | 登录用户 | 修改自己的密码 |

### POST `/api/auth/login`

请求：

```json
{
  "username": "admin",
  "password": "admin123"
}
```

成功响应：

```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "token": "<jwt-token>",
    "token_type": "bearer",
    "user": {
      "uid": "U000001",
      "username": "admin",
      "role": "admin",
      "status": "active",
      "last_login_at": "2026-08-05T10:00:00",
      "created_at": "2026-08-05T10:00:00",
      "updated_at": "2026-08-05T10:00:00"
    }
  }
}
```

前端保存 `data.token`，后续请求放到 `Authorization` 头中。

可能错误：

```text
Invalid username or password
Account is disabled
```

### POST `/api/auth/logout`

请求头：

```http
Authorization: Bearer <token>
```

响应：

```json
{
  "success": true,
  "message": "Logout successful",
  "data": null
}
```

当前后端不会维护 JWT 黑名单。前端收到成功响应后删除本地 token 即可。

### GET `/api/auth/me`

请求头：

```http
Authorization: Bearer <token>
```

响应：

```json
{
  "success": true,
  "message": "Current user fetched successfully",
  "data": {
    "user": {
      "uid": "U000001",
      "username": "admin",
      "role": "admin",
      "status": "active",
      "last_login_at": "2026-08-05T10:00:00",
      "created_at": "2026-08-05T10:00:00",
      "updated_at": "2026-08-05T10:00:00"
    }
  }
}
```

### PATCH `/api/users/me/password`

请求头：

```http
Authorization: Bearer <token>
```

请求：

```json
{
  "old_password": "admin123",
  "new_password": "new-password123"
}
```

响应：

```json
{
  "success": true,
  "message": "Password changed successfully",
  "data": null
}
```

可能错误：

```text
Old password is incorrect
New password must be different from old password
Account is disabled
```

## 用户管理

所有用户管理接口都需要管理员 token。

### 接口列表

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/admin/users` | 创建用户 |
| `GET` | `/api/admin/users` | 获取用户列表 |
| `GET` | `/api/admin/users/{uid}` | 按 `uid` 获取用户 |
| `GET` | `/api/admin/users/by-username/{username}` | 按用户名获取用户 |
| `PATCH` | `/api/admin/users/{uid}/password` | 重置用户密码 |
| `PATCH` | `/api/admin/users/{uid}/role` | 修改用户角色 |
| `PATCH` | `/api/admin/users/{uid}/status` | 修改用户状态 |

### POST `/api/admin/users`

请求：

```json
{
  "username": "test_user",
  "password": "password123",
  "role": "normal"
}
```

字段规则：

| 字段 | 规则 |
| --- | --- |
| `username` | 必填，1-50 字符 |
| `password` | 必填，8-128 字符 |
| `role` | `admin` 或 `normal`，默认 `normal` |

响应：

```json
{
  "success": true,
  "message": "User created successfully",
  "data": null
}
```

### GET `/api/admin/users`

响应：

```json
{
  "success": true,
  "message": "Users fetched successfully",
  "data": {
    "users": [
      {
        "uid": "U000001",
        "username": "admin",
        "role": "admin",
        "status": "active",
        "last_login_at": "2026-08-05T10:00:00",
        "created_at": "2026-08-05T10:00:00",
        "updated_at": "2026-08-05T10:00:00"
      }
    ]
  }
}
```

### GET `/api/admin/users/{uid}`

示例：

```text
GET /api/admin/users/U000002
```

响应中的 `data.user` 与用户对象结构一致。

### GET `/api/admin/users/by-username/{username}`

示例：

```text
GET /api/admin/users/by-username/test_user
```

响应中的 `data.user` 与用户对象结构一致。

### PATCH `/api/admin/users/{uid}/password`

请求：

```json
{
  "new_password": "new-password123"
}
```

响应：

```json
{
  "success": true,
  "message": "User password reset successfully",
  "data": null
}
```

### PATCH `/api/admin/users/{uid}/role`

请求：

```json
{
  "role": "normal"
}
```

如果角色没有变化，也会返回成功：

```text
User role is already up to date
```

### PATCH `/api/admin/users/{uid}/status`

请求：

```json
{
  "status": "disabled"
}
```

如果状态没有变化，也会返回成功：

```text
User status is already up to date
```

## 飞行脚本

飞行脚本用于提交仿真任务。普通用户只能访问自己的 private 脚本和管理员上传的 public 脚本。

脚本对象示例：

```json
{
  "script_code": "F000001",
  "name": "Level Flight Test",
  "original_filename": "level_flight.json",
  "scope": "private",
  "status": "active",
  "description": "Level flight script",
  "created_at": "2026-08-05T10:00:00",
  "updated_at": "2026-08-05T10:00:00"
}
```

### 接口列表

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| `POST` | `/api/scripts` | 登录用户 | 上传自己的 private 脚本 |
| `GET` | `/api/scripts` | 登录用户 | 获取自己可访问的 active 脚本 |
| `GET` | `/api/scripts/{script_code}` | 登录用户 | 获取脚本详情 |
| `GET` | `/api/scripts/{script_code}/download` | 登录用户 | 下载脚本文件 |
| `DELETE` | `/api/scripts/{script_code}` | 登录用户 | 删除自己的 private 脚本 |
| `POST` | `/api/admin/scripts` | 管理员 | 上传 public 脚本 |
| `GET` | `/api/admin/scripts` | 管理员 | 获取所有脚本 |
| `GET` | `/api/admin/scripts/{script_code}` | 管理员 | 获取任意脚本详情 |
| `PATCH` | `/api/admin/scripts/{script_code}` | 管理员 | 修改脚本元信息 |
| `DELETE` | `/api/admin/scripts/{script_code}` | 管理员 | 删除任意脚本 |

### POST `/api/scripts`

请求类型：

```text
multipart/form-data
```

表单字段：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `name` | 是 | 脚本名称 |
| `description` | 否 | 脚本说明 |
| `file` | 是 | 脚本文件 |

响应：

```json
{
  "success": true,
  "message": "Script uploaded successfully",
  "data": {
    "script": {
      "script_code": "F000001",
      "name": "Level Flight Test",
      "original_filename": "flight_script.json",
      "scope": "private",
      "status": "active",
      "description": "Level flight script",
      "created_at": "2026-08-05T10:00:00",
      "updated_at": "2026-08-05T10:00:00"
    }
  }
}
```

### GET `/api/scripts`

响应：

```json
{
  "success": true,
  "message": "Scripts fetched successfully",
  "data": {
    "scripts": [
      {
        "script_code": "F000001",
        "name": "Level Flight Test",
        "original_filename": "flight_script.json",
        "scope": "private",
        "status": "active",
        "description": "Level flight script",
        "created_at": "2026-08-05T10:00:00",
        "updated_at": "2026-08-05T10:00:00"
      }
    ]
  }
}
```

### GET `/api/scripts/{script_code}`

响应中的 `data.script` 与脚本对象结构一致。

### GET `/api/scripts/{script_code}/download`

返回文件流，不是 JSON。前端可用浏览器下载能力保存文件。

### DELETE `/api/scripts/{script_code}`

只能删除当前用户自己的 private 脚本。响应：

```json
{
  "success": true,
  "message": "Script deleted successfully",
  "data": null
}
```

### POST `/api/admin/scripts`

管理员上传 public 脚本。请求类型和字段同 `POST /api/scripts`。

### GET `/api/admin/scripts`

查询参数：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `include_deleted` | `false` | 是否包含已删除脚本 |

示例：

```text
GET /api/admin/scripts?include_deleted=false
```

### PATCH `/api/admin/scripts/{script_code}`

请求字段均可选，但至少传一个：

```json
{
  "name": "Updated Script Name",
  "description": "Updated description",
  "status": "active",
  "scope": "public"
}
```

可选值：

| 字段 | 可选值 |
| --- | --- |
| `status` | `active`, `disabled`, `deleted` |
| `scope` | `private`, `public` |

## 模型管理

模型管理分两类：

| 类型 | 接口 | 用途 |
| --- | --- | --- |
| 管理员接口 | `/api/model-versions` | 上传模型、管理模型、授权用户 |
| 用户接口 | `/api/model-versions/accessible` | 获取当前用户可用模型列表 |

当前仿真可直接加载的本地模型是动态库文件，例如 `.so`、`.dll`、`.dylib`。

访问规则：

- 管理员可以使用所有 active 模型。
- 普通用户可以使用 `access_scope = "all_users"` 的 active 模型。
- 普通用户也可以使用已单独授权且 `can_use = true` 的 private 模型。

模型对象示例：

```json
{
  "version": "v1.0.0",
  "model_name": "Flight Model A",
  "description": "Baseline model",
  "status": "active",
  "access_scope": "private",
  "created_by_uid": "U000001",
  "created_by_username": "admin",
  "created_at": "2026-08-05T10:00:00",
  "updated_at": "2026-08-05T10:00:00"
}
```

### 接口列表

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| `POST` | `/api/model-versions` | 管理员 | 上传并创建模型版本 |
| `GET` | `/api/model-versions` | 管理员 | 获取模型版本列表 |
| `GET` | `/api/model-versions/accessible` | 登录用户 | 获取当前用户可用模型 |
| `PATCH` | `/api/model-versions/{version}` | 管理员 | 修改模型元信息 |
| `GET` | `/api/model-versions/{version}/permissions` | 管理员 | 获取模型授权记录 |
| `POST` | `/api/model-versions/{version}/permissions` | 管理员 | 给一个用户授权 |
| `POST` | `/api/model-versions/{version}/permissions/revoke` | 管理员 | 撤销一个用户授权 |

### POST `/api/model-versions`

请求类型：

```text
multipart/form-data
```

表单字段：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `version` | 是 | 模型版本号，例如 `v1.0.0` |
| `model_name` | 是 | 模型展示名 |
| `file` | 是 | 模型文件 |
| `description` | 否 | 模型说明 |
| `access_scope` | 否 | `private` 或 `all_users`，默认 `private` |

响应：

```json
{
  "success": true,
  "message": "Model version created successfully",
  "data": null
}
```

### GET `/api/model-versions`

查询参数：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `include_disabled` | `true` | 是否包含 disabled 模型 |

响应：

```json
{
  "success": true,
  "message": "Model versions fetched successfully",
  "data": {
    "models": [
      {
        "version": "v1.0.0",
        "model_name": "Flight Model A",
        "description": "Baseline model",
        "status": "active",
        "access_scope": "private",
        "created_by_uid": "U000001",
        "created_by_username": "admin",
        "created_at": "2026-08-05T10:00:00",
        "updated_at": "2026-08-05T10:00:00"
      }
    ]
  }
}
```

### GET `/api/model-versions/accessible`

返回当前登录用户可使用的 active 模型。前端模型选择器应使用这个接口。

### PATCH `/api/model-versions/{version}`

请求字段均可选，但至少传一个：

```json
{
  "version": "v1.0.1",
  "model_name": "Flight Model A Updated",
  "description": "Updated baseline model",
  "status": "active",
  "access_scope": "all_users"
}
```

### GET `/api/model-versions/{version}/permissions`

响应：

```json
{
  "success": true,
  "message": "Model version permissions fetched successfully",
  "data": {
    "permissions": [
      {
        "model_version": "v1.0.0",
        "user_uid": "U000002",
        "username": "test_user",
        "role": "normal",
        "user_status": "active",
        "can_use": true,
        "granted_by_uid": "U000001",
        "granted_by_username": "admin",
        "created_at": "2026-08-05T10:00:00",
        "updated_at": "2026-08-05T10:00:00"
      }
    ]
  }
}
```

### POST `/api/model-versions/{version}/permissions`

请求：

```json
{
  "user_uid": "U000002"
}
```

响应：

```json
{
  "success": true,
  "message": "Model version access granted successfully",
  "data": null
}
```

### POST `/api/model-versions/{version}/permissions/revoke`

请求：

```json
{
  "user_uid": "U000002"
}
```

响应：

```json
{
  "success": true,
  "message": "Model version access revoked successfully",
  "data": null
}
```

## 仿真任务

仿真任务可以指定 `model_version`。如果不传，后端使用默认 `python_mock` 模型。

提交仿真前，前端可以先调用 `GET /api/model-versions/accessible` 获取当前用户可选模型，并把选中模型的 `version` 作为 `model_version` 传入。

目前可用输出参数：

```text
time_s
altitude_m
speed_kmh
pitch_deg
roll_deg
x_m
y_m
```

任务状态：

| 状态 | 含义 |
| --- | --- |
| `queued` | 已排队 |
| `running` | 正在运行 |
| `reporting` | 正在生成报告 |
| `succeeded` | 成功 |
| `succeeded_with_warnings` | 部分试验点失败，但仍生成结果 |
| `failed` | 失败 |
| `cancelled` | 已取消 |

任务对象示例：

如果提交时没有传 `model_version`，任务里的 `model_version` 会是 `null`。

```json
{
  "task_code": "T000001",
  "user_uid": "U000002",
  "script_code": "F000001",
  "subject": "Level Flight",
  "model_version": "v1.0.0",
  "model_name": "Flight Model A",
  "report_template_code": "standard",
  "output_parameters": ["time_s", "altitude_m", "speed_kmh"],
  "status": "running",
  "progress": 42,
  "failed_points": 0,
  "message": "Running TP001",
  "error_message": null,
  "submitted_at": "2026-08-05T10:00:00",
  "started_at": "2026-08-05T10:00:01",
  "finished_at": null,
  "updated_at": "2026-08-05T10:00:05",
  "artifacts": []
}
```

### 接口列表

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| `POST` | `/api/simulations` | 登录用户 | 提交仿真任务 |
| `GET` | `/api/simulations` | 登录用户 | 获取当前用户任务列表 |
| `GET` | `/api/simulations/{task_code}` | 登录用户 | 获取任务状态 |
| `GET` | `/api/simulations/{task_code}/result` | 登录用户 | 获取仿真结果 JSON |
| `GET` | `/api/simulations/{task_code}/report` | 登录用户 | 下载报告 HTML |
| `POST` | `/api/simulations/{task_code}/cancel` | 登录用户 | 请求取消任务 |

### POST `/api/simulations`

请求：

```json
{
  "script_code": "F000001",
  "model_version": "v1.0.0",
  "report_template_code": "standard",
  "output_parameters": ["time_s", "altitude_m", "speed_kmh"],
  "timeout_seconds": 3600
}
```

字段规则：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `script_code` | 是 | 当前用户可访问的脚本编号 |
| `model_version` | 否 | 当前用户可访问的模型版本；不传则使用默认 `python_mock` 模型 |
| `report_template_code` | 否 | 默认 `standard`，不能为空字符串 |
| `output_parameters` | 否 | 输出参数数组；不传或空数组表示输出全部参数 |
| `timeout_seconds` | 否 | 1-86400，默认 3600 |

响应：

```json
{
  "success": true,
  "message": "Simulation task queued",
  "data": {
    "task": {
      "task_code": "T000001",
      "user_uid": "U000002",
      "script_code": "F000001",
      "subject": "Level Flight",
      "model_version": "v1.0.0",
      "model_name": "Flight Model A",
      "report_template_code": "standard",
      "output_parameters": ["time_s", "altitude_m", "speed_kmh"],
      "status": "queued",
      "progress": 0,
      "failed_points": 0,
      "message": "Simulation task queued",
      "error_message": null,
      "submitted_at": "2026-08-05T10:00:00",
      "started_at": null,
      "finished_at": null,
      "updated_at": "2026-08-05T10:00:00",
      "artifacts": []
    }
  }
}
```

可能错误：

```text
Script does not exist
Script file does not exist
$: Flight script file must be valid JSON
<path>: <script validation error>
Default simulation model is not configured
Model version does not exist or is not accessible
Selected model file does not exist
Selected model file type is not supported by simulation
```

### GET `/api/simulations`

获取当前用户自己的任务列表。响应：

```json
{
  "success": true,
  "message": "Simulation tasks fetched successfully",
  "data": {
    "tasks": [
      {
        "task_code": "T000001",
        "user_uid": "U000002",
        "script_code": "F000001",
        "subject": "Level Flight",
        "model_version": "v1.0.0",
        "model_name": "Flight Model A",
        "report_template_code": "standard",
        "output_parameters": ["time_s", "altitude_m", "speed_kmh"],
        "status": "succeeded",
        "progress": 100,
        "failed_points": 0,
        "message": "Simulation finished",
        "error_message": null,
        "submitted_at": "2026-08-05T10:00:00",
        "started_at": "2026-08-05T10:00:01",
        "finished_at": "2026-08-05T10:00:08",
        "updated_at": "2026-08-05T10:00:08",
        "artifacts": []
      }
    ]
  }
}
```

### GET `/api/simulations/{task_code}`

获取单个任务状态。前端提交任务后，可以每 1-2 秒轮询这个接口，直到 `status` 进入终态：

```text
succeeded
succeeded_with_warnings
failed
cancelled
```

响应中的 `data.task` 与任务对象结构一致。

### GET `/api/simulations/{task_code}/result`

如果任务还没生成结果，返回空结果：

```json
{
  "success": true,
  "message": "Simulation result fetched successfully",
  "data": {
    "result": {
      "task": {
        "task_code": "T000001",
        "status": "running",
        "progress": 42
      },
      "points": [],
      "series": [],
      "errors": []
    }
  }
}
```

任务完成后，返回：

```json
{
  "success": true,
  "message": "Simulation result fetched successfully",
  "data": {
    "result": {
      "subject": "Level Flight",
      "script_code": "F000001",
      "model": {
        "model_name": "Flight Model A",
        "model_type": "native",
        "model_version": "v1.0.0",
        "interface_version": "1.0"
      },
      "points": [
        {
          "id": "TP001",
          "status": "success",
          "samples": 121,
          "max_altitude_m": 1012.0,
          "max_speed_kmh": 253.0
        }
      ],
      "series": [
        {
          "point_id": "TP001",
          "time_s": 0.0,
          "altitude_m": 1000.0,
          "speed_kmh": 250.0
        }
      ],
      "errors": [],
      "task": {
        "task_code": "T000001",
        "status": "succeeded",
        "progress": 100
      }
    }
  }
}
```

说明：

- `points` 是每个试验点的摘要。
- `series` 是时间序列数据，字段受 `output_parameters` 控制。
- `errors` 是失败试验点列表。

### GET `/api/simulations/{task_code}/report`

下载 HTML 报告文件。该接口返回文件流，不是 JSON。

如果报告不存在，返回：

```json
{
  "success": false,
  "message": "Simulation report does not exist",
  "data": null
}
```

### POST `/api/simulations/{task_code}/cancel`

请求取消未完成任务。

响应：

```json
{
  "success": true,
  "message": "Simulation cancellation requested",
  "data": null
}
```

如果任务已经完成或无法取消，返回 `409`：

```json
{
  "success": false,
  "message": "Simulation task cannot be cancelled",
  "data": null
}
```

注意：取消会在试验点边界生效，不能强制中断正在运行的原生动态库函数。
