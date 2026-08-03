# Frontend API Integration Guide

## Base URL

During local development, run the backend on the host machine:

```bash
conda run -n flight_web python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Frontend requests should use:

```text
http://<backend-host-ip>:8000
```

Examples:

```text
http://127.0.0.1:8000
http://192.168.x.x:8000
```

Use `127.0.0.1` only when the frontend runs on the same machine as the backend. If another developer connects from a different machine on the same network, use the backend machine's LAN IP.

## Common Rules

All request and response bodies are JSON.

Request header:

```http
Content-Type: application/json
```

New auth and admin user APIs return:

```json
{
  "success": true,
  "message": "Operation message",
  "data": {}
}
```

Errors use the same JSON shape with an appropriate HTTP status code.

Authenticated requests should include:

```http
Authorization: Bearer <token>
```

Model version APIs have not been moved to the authenticated route structure yet. They will be updated separately.

## User Roles and Status

User objects include both:

```text
id: internal database primary key
uid: fixed-width display/API identifier, such as U000001
```

For an existing database, run these migrations before deploying this code:

```text
docs/migrations/20260729_add_user_uid.sql
docs/migrations/20260729_add_user_last_login_at.sql
docs/migrations/20260729_create_flight_scripts.sql
docs/migrations/20260801_create_simulation_tasks.sql
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

## Login

### POST `/api/auth/login`

Request:

```json
{
  "username": "admin",
  "password": "<admin-password>"
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

Failure response:

```json
{
  "success": false,
  "message": "Invalid username or password",
  "data": null
}
```

Possible failure messages:

```text
Invalid username or password
Account is disabled
```

Frontend usage:

After successful login, store the token and user in frontend state. Send the token in the `Authorization` header for authenticated requests. If `user.role` is `admin`, show user management and model management pages. If `user.role` is `normal`, show only ordinary user features.

### POST `/api/auth/logout`

Logout the current user.

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

This endpoint does not revoke the JWT on the backend yet. The frontend should delete the stored token after a successful response.

### GET `/api/auth/me`

Get the current logged-in user.

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

Change the current user's password.

Headers:

```http
Authorization: Bearer <token>
```

Request:

```json
{
  "old_password": "old-password",
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

## User Management

All user management APIs require an admin token.

### POST `/api/admin/users`

Create a user.

Request:

```json
{
  "username": "user1",
  "password": "password123",
  "role": "normal"
}
```

Response:

```json
{
  "success": true,
  "message": "User created successfully",
  "data": null
}
```

Duplicate username response:

```json
{
  "success": false,
  "message": "Username already exists",
  "data": null
}
```

### GET `/api/admin/users`

List all users.

Response:

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

Get one user by username.

Response:

```json
{
  "success": true,
  "message": "User found",
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

### GET `/api/admin/users/{uid}`

Get one user by UID.

Response:

```json
{
  "success": true,
  "message": "User found",
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

### PATCH `/api/admin/users/{uid}/password`

Reset a user's password. Admin token required.

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

Update a user's role.

Request:

```json
{
  "role": "admin"
}
```

Response:

```json
{
  "success": true,
  "message": "User role updated successfully",
  "data": null
}
```

### PATCH `/api/admin/users/{uid}/status`

Enable or disable a user.

Request:

```json
{
  "status": "disabled"
}
```

Response:

```json
{
  "success": true,
  "message": "User status updated successfully",
  "data": null
}
```

Recommended frontend interaction:

- User management table with columns: ID, username, role, status, created time, updated time.
- Create user dialog with username, password, role.
- Role selector for `admin` / `normal`.
- Status toggle for `active` / `disabled`.

## Flight Scripts

Script files are stored under `data/` by default:

```text
data/users/U000001/scripts/F000001.py
data/public/scripts/F000002.py
```

Script objects use `script_code` as the external identifier.

### POST `/api/scripts`

Upload a private script for the current user. Use `multipart/form-data`.

Fields:

```text
name: user-facing script name
description: optional description
file: script file
```

Response:

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

List scripts available to the current user: public scripts plus the user's own private scripts.

### GET `/api/scripts/{script_code}`

Get one accessible script.

### GET `/api/scripts/{script_code}/download`

Download one accessible script file.

### DELETE `/api/scripts/{script_code}`

Soft-delete the current user's own private script.

### POST `/api/admin/scripts`

Upload a public script. Admin token required. Use `multipart/form-data` with the same fields as `POST /api/scripts`.

### GET `/api/admin/scripts`

List all non-deleted scripts. Use `include_deleted=true` to include deleted scripts.

### GET `/api/admin/scripts/{script_code}`

Get one script as admin.

### PATCH `/api/admin/scripts/{script_code}`

Update script metadata as admin.

Request:

```json
{
  "name": "Updated Landing Case",
  "description": "Updated description",
  "scope": "public",
  "status": "active"
}
```

### DELETE `/api/admin/scripts/{script_code}`

Soft-delete any script as admin.

## Model Access Rules

Valid model statuses:

```text
active
disabled
```

Valid access scopes:

```text
private
all_users
```

Access behavior:

- `admin` users can use every active model.
- `normal` users can use active models with `access_scope = "all_users"`.
- `normal` users can also use private models if they have a permission record with `can_use = 1`.

## Model Management

### POST `/api/model-versions`

Create a model version.

Request:

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

Response:

```json
{
  "success": true,
  "message": "Model version created successfully"
}
```

Use `"access_scope": "all_users"` when every active user should be able to use the model without individual authorization.

### GET `/api/model-versions`

List model versions.

Query parameters:

```text
include_disabled=true
include_disabled=false
```

Example:

```text
GET /api/model-versions?include_disabled=true
```

Response:

```json
{
  "success": true,
  "models": [
    {
      "id": 1,
      "version": "v1.0.0",
      "model_name": "Flight Model A",
      "model_path": "/models/flight_model_a.pkl",
      "description": "Baseline model",
      "status": "active",
      "access_scope": "private",
      "created_by": 1,
      "created_at": "2026-07-24T10:00:00",
      "updated_at": "2026-07-24T10:00:00"
    }
  ]
}
```

### GET `/api/model-versions/accessible`

List model versions available to a specific user.

Query parameters:

```text
username=user1
```

Example:

```text
GET /api/model-versions/accessible?username=user1
```

Response:

```json
{
  "success": true,
  "models": [
    {
      "id": 1,
      "version": "v1.0.0",
      "model_name": "Flight Model A",
      "model_path": "/models/flight_model_a.pkl",
      "description": "Baseline model",
      "status": "active",
      "access_scope": "all_users"
    }
  ]
}
```

Use this endpoint for the model selector on normal user workflows.

### PATCH `/api/model-versions/{model_version_id}`

Update a model version.

All fields are optional, but at least one field should be provided.

Request:

```json
{
  "model_name": "Flight Model A Updated",
  "description": "Updated baseline model",
  "status": "active",
  "access_scope": "all_users"
}
```

Response:

```json
{
  "success": true,
  "message": "Model version updated successfully"
}
```

### GET `/api/model-versions/{model_version_id}/permissions`

List permission records for a model version.

Response:

```json
{
  "success": true,
  "permissions": [
    {
      "id": 1,
      "model_version_id": 1,
      "user_id": 2,
      "username": "user1",
      "role": "normal",
      "user_status": "active",
      "can_use": 1,
      "granted_by": 1,
      "created_at": "2026-07-24T10:00:00",
      "updated_at": "2026-07-24T10:00:00"
    }
  ]
}
```

### POST `/api/model-versions/{model_version_id}/permissions`

Grant one user access to a private model version.

Request:

```json
{
  "user_id": 2,
  "granted_by": 1
}
```

Response:

```json
{
  "success": true,
  "message": "Model version access granted successfully"
}
```

### POST `/api/model-versions/{model_version_id}/permissions/revoke`

Revoke one user's access to a model version.

Request:

```json
{
  "user_id": 2
}
```

Response:

```json
{
  "success": true,
  "message": "Model version access revoked successfully"
}
```

The revoke operation sets `can_use = 0`; it does not delete the permission record.

Recommended frontend interaction:

- Model management table with columns: version, model name, status, access scope, created by, updated time.
- Create model dialog with version, name, path, description, access scope.
- Access scope control:
  - `private`: show a user permission management panel.
  - `all_users`: show a simple indicator that all active users can use it.
- Permission panel:
  - Show user list.
  - Each user has an allow/revoke control.
  - Call the grant endpoint when enabled.
  - Call the revoke endpoint when disabled.

## Suggested Page Structure

Admin frontend:

```text
Login
User Management
Model Management
```

Normal user frontend:

```text
Login
Simulation page
Model selector from GET /api/model-versions/accessible?username=<username>
```

## JavaScript Examples

Login:

```javascript
async function login(baseUrl, username, password) {
  const response = await fetch(`${baseUrl}/api/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ username, password })
  });

  return response.json();
}
```

Create model version:

```javascript
async function createModelVersion(baseUrl, model) {
  const response = await fetch(`${baseUrl}/api/model-versions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(model)
  });

  return response.json();
}
```

List accessible models:

```javascript
async function listAccessibleModels(baseUrl, username) {
  const url = new URL(`${baseUrl}/api/model-versions/accessible`);
  url.searchParams.set("username", username);

  const response = await fetch(url);
  return response.json();
}
```

## Current Limitations

- Model version APIs have not been migrated to JWT auth yet.
- Some older model version API errors still use `success: false` in the JSON body instead of detailed HTTP status codes.
- Model file upload is not implemented yet; `model_path` is stored as text.

## Simulation Tasks

- `POST /api/simulations`
- `GET /api/simulations`
- `GET /api/simulations/{task_code}`
- `GET /api/simulations/{task_code}/result`
- `GET /api/simulations/{task_code}/report`
- `POST /api/simulations/{task_code}/cancel`

### POST `/api/simulations`

Submit a simulation task. The current backend does not require `model_version_id`; it uses the default `python_mock` model.

Request body:

```json
{
  "script_code": "F000001",
  "output_parameters": ["altitude_m", "speed_kmh"]
}
```

The script file must be FlightScript JSON 1.0:

```json
{
  "schema_version": "1.0",
  "subject": {"code": "level-flight", "name": "Level Flight"},
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

### GET `/api/simulations`

List the current user's simulation tasks.

### GET `/api/simulations/{task_code}`

Fetch a simulation task status.

### GET `/api/simulations/{task_code}/result`

Fetch simulation result summary and time-series data.

### GET `/api/simulations/{task_code}/report`

Download the generated HTML report.

### POST `/api/simulations/{task_code}/cancel`

Request cancellation for an unfinished simulation task. Cancellation is cooperative and takes effect between test points.
