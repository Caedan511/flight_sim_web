# Frontend API Integration Guide

## Base URL

During local development, run the backend on the host machine:

```bash
conda run -n flight_web python -m uvicorn backend.api_server:app --host 0.0.0.0 --port 8000
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

Current API responses usually return HTTP 200 and include:

```json
{
  "success": true,
  "message": "Operation message"
}
```

Login sessions or API tokens are not implemented yet. Admin-only pages should be treated as frontend-only guarded for now, based on the `role` returned by login. Backend permission enforcement should be added later.

## User Roles and Status

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

### POST `/api/login`

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
  "role": "admin"
}
```

Failure response:

```json
{
  "success": false,
  "message": "Incorrect password"
}
```

Possible failure messages:

```text
User does not exist
Account is disabled
Incorrect password
```

Frontend usage:

After successful login, store the username and role in frontend state. If `role` is `admin`, show user management and model management pages. If `role` is `normal`, show only ordinary user features.

## User Management

### POST `/api/users`

Create a user.

Request:

```json
{
  "username": "user1",
  "password": "123456",
  "role": "normal"
}
```

Response:

```json
{
  "success": true,
  "message": "User created successfully"
}
```

### GET `/api/users`

List all users.

Response:

```json
{
  "success": true,
  "users": [
    {
      "id": 1,
      "username": "admin",
      "role": "admin",
      "status": "active",
      "created_at": "2026-07-24T10:00:00",
      "updated_at": "2026-07-24T10:00:00"
    }
  ]
}
```

### GET `/api/users/{user_id}`

Get one user by ID.

Response:

```json
{
  "success": true,
  "message": "User found",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "status": "active",
    "created_at": "2026-07-24T10:00:00",
    "updated_at": "2026-07-24T10:00:00"
  }
}
```

### PATCH `/api/users/{user_id}/role`

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
  "message": "User role updated successfully"
}
```

### PATCH `/api/users/{user_id}/status`

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
  "message": "User status updated successfully"
}
```

Recommended frontend interaction:

- User management table with columns: ID, username, role, status, created time, updated time.
- Create user dialog with username, password, role.
- Role selector for `admin` / `normal`.
- Status toggle for `active` / `disabled`.

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
  const response = await fetch(`${baseUrl}/api/login`, {
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

- No backend login session or API token yet.
- Admin APIs are not protected on the backend yet.
- Password reset/change APIs are not implemented yet.
- API errors currently use `success: false` in the JSON body instead of detailed HTTP status codes.
- Model file upload is not implemented yet; `model_path` is stored as text.
