# Frontend API Integration Guide

## Table of Contents

- [Base URL](#base-url)
- [Default Admin](#default-admin)
- [Common Rules](#common-rules)
- [Public Identifiers](#public-identifiers)
- [Authentication](#authentication)
- [User Management](#user-management)
- [Flight Scripts](#flight-scripts)
- [Model Management](#model-management)
- [Simulation Tasks](#simulation-tasks)

## Base URL

Frontend request base URL:

```text
http://<backend-machine-ip>:8000
```

## Default Admin

Default integration admin account:

```text
username: admin
password: admin123
```

## Common Rules

Except for file upload and file download endpoints, request and response bodies are JSON.

JSON request header:

```http
Content-Type: application/json
```

File upload endpoints use:

```http
Content-Type: multipart/form-data
```

Authenticated endpoints require:

```http
Authorization: Bearer <token>
```

Success response shape:

```json
{
  "success": true,
  "message": "Operation message",
  "data": {}
}
```

Error response shape:

```json
{
  "success": false,
  "message": "Error message",
  "data": null
}
```

Common HTTP status codes:

| Status | Meaning |
| --- | --- |
| `400` | Invalid request or business validation failed |
| `401` | Missing, invalid, or expired token |
| `403` | Logged in but permission denied, or account disabled |
| `404` | Resource does not exist |
| `409` | Operation is not allowed in the current state |

## Public Identifiers

Public APIs use these identifiers:

| Resource | Frontend field | Example |
| --- | --- | --- |
| User | `uid` | `U000001` |
| Flight script | `script_code` | `F000001` |
| Model version | `version` | `v1.0.0` |
| Simulation task | `task_code` | `T000001` |
| Simulation artifact | `artifact_code` | `T000001-report-report` |

User object example:

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

Valid user roles:

```text
admin
normal
```

Valid user statuses:

```text
active
disabled
```

## Authentication

### Endpoint List

| Method | Path | Permission | Description |
| --- | --- | --- | --- |
| `POST` | `/api/auth/login` | None | Log in and get a token |
| `POST` | `/api/auth/logout` | Logged-in user | Clear frontend login state |
| `GET` | `/api/auth/me` | Logged-in user | Get current user |
| `PATCH` | `/api/users/me/password` | Logged-in user | Change own password |

### POST `/api/auth/login`

Request:

```json
{
  "username": "admin",
  "password": "admin123"
}
```

Success response:

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

The frontend should store `data.token` and send it in the `Authorization` header for later requests.

Possible errors:

```text
Invalid username or password
Account is disabled
```

### POST `/api/auth/logout`

Headers:

```http
Authorization: Bearer <token>
```

Response:

```json
{
  "success": true,
  "message": "Logout successful",
  "data": null
}
```

The backend does not maintain a JWT denylist yet. After a successful response, the frontend can delete the local token.

### GET `/api/auth/me`

Headers:

```http
Authorization: Bearer <token>
```

Response:

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

Headers:

```http
Authorization: Bearer <token>
```

Request:

```json
{
  "old_password": "admin123",
  "new_password": "new-password123"
}
```

Response:

```json
{
  "success": true,
  "message": "Password changed successfully",
  "data": null
}
```

Possible errors:

```text
Old password is incorrect
New password must be different from old password
Account is disabled
```

## User Management

All user management endpoints require an admin token.

### Endpoint List

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/admin/users` | Create a user |
| `GET` | `/api/admin/users` | List users |
| `GET` | `/api/admin/users/{uid}` | Get user by `uid` |
| `GET` | `/api/admin/users/by-username/{username}` | Get user by username |
| `PATCH` | `/api/admin/users/{uid}/password` | Reset user password |
| `PATCH` | `/api/admin/users/{uid}/role` | Update user role |
| `PATCH` | `/api/admin/users/{uid}/status` | Update user status |

### POST `/api/admin/users`

Request:

```json
{
  "username": "test_user",
  "password": "password123",
  "role": "normal"
}
```

Field rules:

| Field | Rule |
| --- | --- |
| `username` | Required, 1-50 characters |
| `password` | Required, 8-128 characters |
| `role` | `admin` or `normal`; default `normal` |

Response:

```json
{
  "success": true,
  "message": "User created successfully",
  "data": null
}
```

### GET `/api/admin/users`

Response:

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

Example:

```text
GET /api/admin/users/U000002
```

The response `data.user` has the same shape as the user object.

### GET `/api/admin/users/by-username/{username}`

Example:

```text
GET /api/admin/users/by-username/test_user
```

The response `data.user` has the same shape as the user object.

### PATCH `/api/admin/users/{uid}/password`

Request:

```json
{
  "new_password": "new-password123"
}
```

Response:

```json
{
  "success": true,
  "message": "User password reset successfully",
  "data": null
}
```

### PATCH `/api/admin/users/{uid}/role`

Request:

```json
{
  "role": "normal"
}
```

If the role is already up to date, the endpoint still returns success:

```text
User role is already up to date
```

### PATCH `/api/admin/users/{uid}/status`

Request:

```json
{
  "status": "disabled"
}
```

If the status is already up to date, the endpoint still returns success:

```text
User status is already up to date
```

## Flight Scripts

Flight scripts are used when submitting simulation tasks. A normal user can access their own private scripts and public scripts uploaded by admins.

Script object example:

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

### Endpoint List

| Method | Path | Permission | Description |
| --- | --- | --- | --- |
| `POST` | `/api/scripts` | Logged-in user | Upload a private script |
| `GET` | `/api/scripts` | Logged-in user | List accessible active scripts |
| `GET` | `/api/scripts/{script_code}` | Logged-in user | Get script detail |
| `GET` | `/api/scripts/{script_code}/download` | Logged-in user | Download script file |
| `DELETE` | `/api/scripts/{script_code}` | Logged-in user | Delete own private script |
| `POST` | `/api/admin/scripts` | Admin | Upload a public script |
| `GET` | `/api/admin/scripts` | Admin | List all scripts |
| `GET` | `/api/admin/scripts/{script_code}` | Admin | Get any script detail |
| `PATCH` | `/api/admin/scripts/{script_code}` | Admin | Update script metadata |
| `DELETE` | `/api/admin/scripts/{script_code}` | Admin | Delete any script |

### POST `/api/scripts`

Request content type:

```text
multipart/form-data
```

Form fields:

| Field | Required | Description |
| --- | --- | --- |
| `name` | Yes | Script name |
| `description` | No | Script description |
| `file` | Yes | Script file |

Response:

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

Response:

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

The response `data.script` has the same shape as the script object.

### GET `/api/scripts/{script_code}/download`

Returns a file stream, not JSON. The frontend can use the browser download flow.

### DELETE `/api/scripts/{script_code}`

Only the current user's own private scripts can be deleted. Response:

```json
{
  "success": true,
  "message": "Script deleted successfully",
  "data": null
}
```

### POST `/api/admin/scripts`

Upload a public script as admin. The request content type and fields are the same as `POST /api/scripts`.

### GET `/api/admin/scripts`

Query parameters:

| Parameter | Default | Description |
| --- | --- | --- |
| `include_deleted` | `false` | Whether to include deleted scripts |

Example:

```text
GET /api/admin/scripts?include_deleted=false
```

### PATCH `/api/admin/scripts/{script_code}`

All fields are optional, but at least one field is required:

```json
{
  "name": "Updated Script Name",
  "description": "Updated description",
  "status": "active",
  "scope": "public"
}
```

Allowed values:

| Field | Values |
| --- | --- |
| `status` | `active`, `disabled`, `deleted` |
| `scope` | `private`, `public` |

## Model Management

Model management has two categories:

| Type | Endpoint | Purpose |
| --- | --- | --- |
| Admin endpoints | `/api/model-versions` | Upload models, manage models, grant access |
| User endpoint | `/api/model-versions/accessible` | List models available to the current user |

The current simulation runner can directly load local dynamic library models, such as `.so`, `.dll`, and `.dylib`.

Access rules:

- Admin users can use every active model.
- Normal users can use active models with `access_scope = "all_users"`.
- Normal users can also use private models if they have an explicit permission record with `can_use = true`.

Model object example:

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

### Endpoint List

| Method | Path | Permission | Description |
| --- | --- | --- | --- |
| `POST` | `/api/model-versions` | Admin | Upload and create a model version |
| `GET` | `/api/model-versions` | Admin | List model versions |
| `GET` | `/api/model-versions/accessible` | Logged-in user | List current user's accessible models |
| `PATCH` | `/api/model-versions/{version}` | Admin | Update model metadata |
| `GET` | `/api/model-versions/{version}/permissions` | Admin | List model permission records |
| `POST` | `/api/model-versions/{version}/permissions` | Admin | Grant one user access |
| `POST` | `/api/model-versions/{version}/permissions/revoke` | Admin | Revoke one user's access |

### POST `/api/model-versions`

Request content type:

```text
multipart/form-data
```

Form fields:

| Field | Required | Description |
| --- | --- | --- |
| `version` | Yes | Model version, for example `v1.0.0` |
| `model_name` | Yes | Model display name |
| `file` | Yes | Model file |
| `description` | No | Model description |
| `access_scope` | No | `private` or `all_users`; default `private` |

Response:

```json
{
  "success": true,
  "message": "Model version created successfully",
  "data": null
}
```

### GET `/api/model-versions`

Query parameters:

| Parameter | Default | Description |
| --- | --- | --- |
| `include_disabled` | `true` | Whether to include disabled models |

Response:

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

Returns active models available to the current logged-in user. The frontend model selector should use this endpoint.

### PATCH `/api/model-versions/{version}`

All fields are optional, but at least one field is required:

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

Response:

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

Request:

```json
{
  "user_uid": "U000002"
}
```

Response:

```json
{
  "success": true,
  "message": "Model version access granted successfully",
  "data": null
}
```

### POST `/api/model-versions/{version}/permissions/revoke`

Request:

```json
{
  "user_uid": "U000002"
}
```

Response:

```json
{
  "success": true,
  "message": "Model version access revoked successfully",
  "data": null
}
```

## Simulation Tasks

Simulation tasks can specify `model_version`. If omitted, the backend uses the default `python_mock` model.

Before submitting a simulation, the frontend can call `GET /api/model-versions/accessible` to list models available to the current user, then pass the selected model's `version` as `model_version`.

Available output parameters:

```text
time_s
altitude_m
speed_kmh
pitch_deg
roll_deg
x_m
y_m
```

Task statuses:

| Status | Meaning |
| --- | --- |
| `queued` | Queued |
| `running` | Running |
| `reporting` | Generating report |
| `succeeded` | Finished successfully |
| `succeeded_with_warnings` | Some test points failed, but results were generated |
| `failed` | Failed |
| `cancelled` | Cancelled |

Task object example:

If `model_version` is omitted during submission, the task's `model_version` will be `null`.

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

### Endpoint List

| Method | Path | Permission | Description |
| --- | --- | --- | --- |
| `POST` | `/api/simulations` | Logged-in user | Submit a simulation task |
| `GET` | `/api/simulations` | Logged-in user | List current user's tasks |
| `GET` | `/api/simulations/{task_code}` | Logged-in user | Get task status |
| `GET` | `/api/simulations/{task_code}/result` | Logged-in user | Get simulation result JSON |
| `GET` | `/api/simulations/{task_code}/report` | Logged-in user | Download HTML report |
| `POST` | `/api/simulations/{task_code}/cancel` | Logged-in user | Request cancellation |

### POST `/api/simulations`

Request:

```json
{
  "script_code": "F000001",
  "model_version": "v1.0.0",
  "report_template_code": "standard",
  "output_parameters": ["time_s", "altitude_m", "speed_kmh"],
  "timeout_seconds": 3600
}
```

Field rules:

| Field | Required | Description |
| --- | --- | --- |
| `script_code` | Yes | Script code accessible to the current user |
| `model_version` | No | Model version accessible to the current user; omitted means the default `python_mock` model |
| `report_template_code` | No | Default `standard`; cannot be an empty string |
| `output_parameters` | No | Output parameter array; missing or empty means all parameters |
| `timeout_seconds` | No | 1-86400, default 3600 |

Response:

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

Possible errors:

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

List the current user's simulation tasks. Response:

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

Get one task's status. After submitting a task, the frontend can poll this endpoint every 1-2 seconds until `status` becomes terminal:

```text
succeeded
succeeded_with_warnings
failed
cancelled
```

The response `data.task` has the same shape as the task object.

### GET `/api/simulations/{task_code}/result`

If the result has not been generated yet, the endpoint returns an empty result:

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

After the task finishes, response:

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

Notes:

- `points` is a per-test-point summary.
- `series` is time-series data controlled by `output_parameters`.
- `errors` contains failed test points.

### GET `/api/simulations/{task_code}/report`

Downloads the HTML report file. This endpoint returns a file stream, not JSON.

If the report does not exist:

```json
{
  "success": false,
  "message": "Simulation report does not exist",
  "data": null
}
```

### POST `/api/simulations/{task_code}/cancel`

Request cancellation for an unfinished task.

Response:

```json
{
  "success": true,
  "message": "Simulation cancellation requested",
  "data": null
}
```

If the task has already finished or cannot be cancelled, the backend returns `409`:

```json
{
  "success": false,
  "message": "Simulation task cannot be cancelled",
  "data": null
}
```

Note: cancellation takes effect between test points. It cannot forcibly interrupt a running native library function.
