# 前端 API 对接指南

## 基础地址


前端请求地址：

```text
http://<后端机器 IP>:8000
```


## 通用规则

除文件上传接口外，请求和响应主体均为 JSON。

JSON 请求头：

```http
Content-Type: application/json
```

新的认证接口和管理员用户接口统一返回：

```json
{
  "success": true,
  "message": "操作信息",
  "data": {}
}
```

错误响应也使用同样结构，并配合合适的 HTTP 状态码。

需要登录的接口必须携带：

```http
Authorization: Bearer <token>
```

模型版本接口暂时还没有迁移到 JWT 鉴权结构，后续会单独调整。

## 用户角色和状态

用户对象同时包含：

```text
id: 数据库内部自增主键
uid: 前端展示和接口使用的定长用户标识，例如 U000001
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

### POST `/api/auth/login`

请求：

```json
{
  "username": "admin",
  "password": "<admin-password>"
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
      "id": 1,
      "uid": "U000001",
      "username": "admin",
      "role": "admin",
      "status": "active",
      "last_login_at": "2026-07-24T10:00:00"
    }
  }
}
```

失败响应：

```json
{
  "success": false,
  "message": "Invalid username or password",
  "data": null
}
```

可能的失败信息：

```text
Invalid username or password
Account is disabled
```

前端用法：

登录成功后，在前端状态中保存 `token` 和 `user`。后续需要登录的请求，在 `Authorization` 头中携带 token。若 `user.role` 为 `admin`，展示用户管理、模型管理等管理员页面；若为 `normal`，只展示普通用户功能。

### POST `/api/auth/logout`

退出当前用户。

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

当前接口不会在后端撤销 JWT。前端收到成功响应后，删除本地保存的 token 即可。

### GET `/api/auth/me`

获取当前登录用户信息。

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
      "id": 1,
      "uid": "U000001",
      "username": "admin",
      "role": "admin",
      "status": "active",
      "last_login_at": "2026-07-24T10:00:00",
      "created_at": "2026-07-24T10:00:00",
      "updated_at": "2026-07-24T10:00:00"
    }
  }
}
```

### PATCH `/api/users/me/password`

当前用户修改自己的密码。

请求头：

```http
Authorization: Bearer <token>
```

请求：

```json
{
  "old_password": "old-password",
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

## 用户管理

所有用户管理接口都需要管理员 token。

### POST `/api/admin/users`

创建用户。

请求：

```json
{
  "username": "user1",
  "password": "password123",
  "role": "normal"
}
```

响应：

```json
{
  "success": true,
  "message": "User created successfully",
  "data": null
}
```

用户名重复时：

```json
{
  "success": false,
  "message": "Username already exists",
  "data": null
}
```

### GET `/api/admin/users`

获取所有用户。

响应：

```json
{
  "success": true,
  "message": "Users fetched successfully",
  "data": {
    "users": [
      {
        "id": 1,
        "uid": "U000001",
        "username": "admin",
        "role": "admin",
        "status": "active",
        "last_login_at": "2026-07-24T10:00:00",
        "created_at": "2026-07-24T10:00:00",
        "updated_at": "2026-07-24T10:00:00"
      }
    ]
  }
}
```

### GET `/api/admin/users/by-username/{username}`

按用户名查询一个用户。

### GET `/api/admin/users/{uid}`

按 UID 查询一个用户。

### PATCH `/api/admin/users/{uid}/password`

管理员重置用户密码。

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

修改用户角色。

请求：

```json
{
  "role": "admin"
}
```

响应：

```json
{
  "success": true,
  "message": "User role updated successfully",
  "data": null
}
```

### PATCH `/api/admin/users/{uid}/status`

启用或禁用用户。

请求：

```json
{
  "status": "disabled"
}
```

响应：

```json
{
  "success": true,
  "message": "User status updated successfully",
  "data": null
}
```


## 飞行脚本

脚本文件默认保存在 `data/` 下：

```text
data/users/U000001/scripts/F000001.py
data/public/scripts/F000002.py
```

脚本对象使用 `script_code` 作为对外标识。

### POST `/api/scripts`

当前用户上传私有脚本。请求类型为 `multipart/form-data`。

字段：

```text
name: 用户输入的脚本名称
description: 可选描述
file: 脚本文件
```

响应：

```json
{
  "success": true,
  "message": "Script uploaded successfully",
  "data": {
    "script": {
      "id": 1,
      "script_code": "F000001",
      "owner_user_id": 2,
      "name": "Landing Case A",
      "original_filename": "landing_case_a.py",
      "file_path": "data/users/U000002/scripts/F000001.py",
      "scope": "private",
      "status": "active",
      "description": "Landing simulation input",
      "created_at": "2026-07-24T10:00:00",
      "updated_at": "2026-07-24T10:00:00"
    }
  }
}
```

### GET `/api/scripts`

获取当前用户可用脚本：公共脚本 + 当前用户自己的私有脚本。

请求头：

```http
Authorization: Bearer <token>
```

响应：

```json
{
  "success": true,
  "message": "Scripts fetched successfully",
  "data": {
    "scripts": [
      {
        "id": 1,
        "script_code": "F000001",
        "owner_user_id": 2,
        "name": "Landing Case A",
        "original_filename": "landing_case_a.py",
        "file_path": "data/users/U000002/scripts/F000001.py",
        "scope": "private",
        "status": "active",
        "description": "Landing simulation input",
        "created_at": "2026-07-24T10:00:00",
        "updated_at": "2026-07-24T10:00:00"
      },
      {
        "id": 2,
        "script_code": "F000002",
        "owner_user_id": 1,
        "name": "Public Baseline Script",
        "original_filename": "baseline.py",
        "file_path": "data/public/scripts/F000002.py",
        "scope": "public",
        "status": "active",
        "description": "Shared baseline script",
        "created_at": "2026-07-24T10:00:00",
        "updated_at": "2026-07-24T10:00:00"
      }
    ]
  }
}
```

### GET `/api/scripts/{script_code}`

获取一个当前用户可访问的脚本。

请求头：

```http
Authorization: Bearer <token>
```

路径参数：

```text
script_code: 脚本编号，例如 F000001
```

响应：

```json
{
  "success": true,
  "message": "Script found",
  "data": {
    "script": {
      "id": 1,
      "script_code": "F000001",
      "owner_user_id": 2,
      "name": "Landing Case A",
      "original_filename": "landing_case_a.py",
      "file_path": "data/users/U000002/scripts/F000001.py",
      "scope": "private",
      "status": "active",
      "description": "Landing simulation input",
      "created_at": "2026-07-24T10:00:00",
      "updated_at": "2026-07-24T10:00:00"
    }
  }
}
```

如果脚本不存在，或当前用户没有访问权限，返回 `404`。

### GET `/api/scripts/{script_code}/download`

下载一个当前用户可访问的脚本文件。

请求头：

```http
Authorization: Bearer <token>
```

路径参数：

```text
script_code: 脚本编号，例如 F000001
```

响应为文件流，下载文件名使用 `original_filename`。如果脚本不存在、当前用户无权访问，或服务器上的脚本文件不存在，返回 `404`。

### DELETE `/api/scripts/{script_code}`

软删除当前用户自己的私有脚本。

请求头：

```http
Authorization: Bearer <token>
```

路径参数：

```text
script_code: 脚本编号，例如 F000001
```

响应：

```json
{
  "success": true,
  "message": "Script deleted successfully",
  "data": null
}
```

普通用户只能删除自己上传的私有脚本，不能删除公共脚本，也不能删除其他用户的私有脚本。

### POST `/api/admin/scripts`

管理员上传公共脚本。需要管理员 token。请求类型和字段同 `POST /api/scripts`。

请求头：

```http
Authorization: Bearer <admin-token>
```

请求类型：

```http
Content-Type: multipart/form-data
```

字段：

```text
name: 脚本名称，必填
description: 脚本描述，可选
file: 脚本文件，必填
```

响应：

```json
{
  "success": true,
  "message": "Script uploaded successfully",
  "data": {
    "script": {
      "id": 2,
      "script_code": "F000002",
      "owner_user_id": 1,
      "name": "Public Baseline Script",
      "original_filename": "baseline.py",
      "file_path": "data/public/scripts/F000002.py",
      "scope": "public",
      "status": "active",
      "description": "Shared baseline script",
      "created_at": "2026-07-24T10:00:00",
      "updated_at": "2026-07-24T10:00:00"
    }
  }
}
```

### GET `/api/admin/scripts`

管理员获取所有未删除脚本。传 `include_deleted=true` 时包含已删除脚本。

请求头：

```http
Authorization: Bearer <admin-token>
```

查询参数：

```text
include_deleted=false
include_deleted=true
```

响应：

```json
{
  "success": true,
  "message": "Scripts fetched successfully",
  "data": {
    "scripts": [
      {
        "id": 1,
        "script_code": "F000001",
        "owner_user_id": 2,
        "name": "Landing Case A",
        "original_filename": "landing_case_a.py",
        "file_path": "data/users/U000002/scripts/F000001.py",
        "scope": "private",
        "status": "active",
        "description": "Landing simulation input",
        "created_at": "2026-07-24T10:00:00",
        "updated_at": "2026-07-24T10:00:00"
      }
    ]
  }
}
```

### GET `/api/admin/scripts/{script_code}`

管理员获取一个脚本。

请求头：

```http
Authorization: Bearer <admin-token>
```

路径参数：

```text
script_code: 脚本编号，例如 F000001
```

响应：

```json
{
  "success": true,
  "message": "Script found",
  "data": {
    "script": {
      "id": 1,
      "script_code": "F000001",
      "owner_user_id": 2,
      "name": "Landing Case A",
      "original_filename": "landing_case_a.py",
      "file_path": "data/users/U000002/scripts/F000001.py",
      "scope": "private",
      "status": "active",
      "description": "Landing simulation input",
      "created_at": "2026-07-24T10:00:00",
      "updated_at": "2026-07-24T10:00:00"
    }
  }
}
```

### PATCH `/api/admin/scripts/{script_code}`

管理员修改脚本元信息。

请求头：

```http
Authorization: Bearer <admin-token>
```

路径参数：

```text
script_code: 脚本编号，例如 F000001
```

所有字段都是可选字段，但至少需要传一个字段。

可用字段：

```text
name: 脚本名称
description: 脚本描述
scope: private 或 public
status: active、disabled 或 deleted
```

请求：

```json
{
  "name": "Updated Landing Case",
  "description": "Updated description",
  "scope": "public",
  "status": "active"
}
```

响应：

```json
{
  "success": true,
  "message": "Script updated successfully",
  "data": null
}
```

### DELETE `/api/admin/scripts/{script_code}`

管理员软删除任意脚本。

请求头：

```http
Authorization: Bearer <admin-token>
```

路径参数：

```text
script_code: 脚本编号，例如 F000001
```

响应：

```json
{
  "success": true,
  "message": "Script deleted successfully",
  "data": null
}
```

## 模型访问规则

有效模型状态：

```text
active
disabled
```

有效访问范围：

```text
private
all_users
```

访问规则：

- 管理员可以使用所有 active 模型。
- 普通用户可以使用 `access_scope = "all_users"` 的 active 模型。
- 普通用户也可以使用已单独授权且 `can_use = 1` 的 private 模型。

## 模型管理

模型版本接口暂时保持旧结构，后续会统一迁移到 JWT 鉴权和新的返回格式。

### POST `/api/model-versions`

创建模型版本。

请求：

```json
{
  "version": "v1.0.0",
  "model_name": "Flight Model A",
  "model_path": "/models/flight_model_a.pkl",
  "description": "Baseline model",
  "access_scope": "private",
  "created_by": 1
}
```

### GET `/api/model-versions`

获取模型版本列表。

查询参数：

```text
include_disabled=true
include_disabled=false
```

### GET `/api/model-versions/accessible`

获取指定用户名可访问的模型版本。

查询参数：

```text
username=user1
```

### PATCH `/api/model-versions/{model_version_id}`

更新模型版本。

### GET `/api/model-versions/{model_version_id}/permissions`

获取某个模型版本的授权记录。

### POST `/api/model-versions/{model_version_id}/permissions`

给用户授权某个模型版本。

请求：

```json
{
  "user_id": 2,
  "granted_by": 1
}
```

### POST `/api/model-versions/{model_version_id}/permissions/revoke`

撤销用户对某个模型版本的授权。

请求：

```json
{
  "user_id": 2
}
```

## 仿真任务

- `POST /api/simulations`
- `GET /api/simulations`
- `GET /api/simulations/{task_code}`
- `GET /api/simulations/{task_code}/result`
- `GET /api/simulations/{task_code}/report`
- `POST /api/simulations/{task_code}/cancel`

### POST `/api/simulations`

提交一个仿真任务。当前阶段不需要前端传 `model_version_id`，后端默认使用 `python_mock` 模型。

请求体：

```json
{
  "script_code": "F000001",
  "output_parameters": ["altitude_m", "speed_kmh"]
}
```

脚本文件必须是 FlightScript JSON 1.0 格式，至少包含：

```json
{
  "schema_version": "1.0",
  "subject": {"code": "level-flight", "name": "定常平飞"},
  "test_points": [
    {
      "id": "TP-001",
      "initial_conditions": {
        "altitude_m": 5000,
        "speed_kmh": 450
      },
      "duration_s": 60
    }
  ]
}
```

响应：

```json
{
  "success": true,
  "message": "Simulation task queued",
  "data": {
    "task": {
      "task_code": "T000001",
      "script_code": "F000001",
      "status": "queued",
      "progress": 0
    }
  }
}
```

### GET `/api/simulations`

获取当前用户自己的仿真任务列表。

### GET `/api/simulations/{task_code}`

获取当前用户某个仿真任务的状态和进度。

### GET `/api/simulations/{task_code}/result`

获取仿真结果摘要和时间序列数据。

### GET `/api/simulations/{task_code}/report`

下载仿真报告 HTML 文件。

### POST `/api/simulations/{task_code}/cancel`

请求取消未完成的仿真任务。取消在试验点边界生效，不能强制中断正在运行的原生动态库函数。
