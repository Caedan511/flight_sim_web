from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.auth_service import (
    authenticate_user,
    create_user,
    get_user_by_id,
    list_users,
    update_user_role,
    update_user_status,
)
from backend.model_service import (
    create_model_version,
    grant_model_version_access,
    list_accessible_model_versions,
    list_model_version_permissions,
    list_model_versions,
    revoke_model_version_access,
    update_model_version,
)
from config import Config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "normal"


class UpdateUserRoleRequest(BaseModel):
    role: str


class UpdateUserStatusRequest(BaseModel):
    status: str


class CreateModelVersionRequest(BaseModel):
    version: str
    model_name: str
    model_path: str
    description: Optional[str] = None
    access_scope: str = "private"
    created_by: Optional[int] = None


class UpdateModelVersionRequest(BaseModel):
    version: Optional[str] = None
    model_name: Optional[str] = None
    model_path: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    access_scope: Optional[str] = None


class GrantModelAccessRequest(BaseModel):
    user_id: int
    granted_by: Optional[int] = None


@app.post("/api/login")
def login(data: LoginRequest):
    success, result = authenticate_user(data.username, data.password)

    if success:
        return {
            "success": True,
            "message": "Login successful",
            "role": result
        }
    else:
        return {
            "success": False,
            "message": result
        }


@app.post("/api/users")
def create_user_api(data: CreateUserRequest):
    success, message = create_user(data.username, data.password, data.role)

    return {
        "success": success,
        "message": message
    }


@app.get("/api/users")
def list_users_api():
    return {
        "success": True,
        "users": list_users()
    }


@app.get("/api/users/{user_id}")
def get_user_api(user_id: int):
    user = get_user_by_id(user_id)

    return {
        "success": user is not None,
        "user": user,
        "message": "User found" if user is not None else "User does not exist"
    }


@app.patch("/api/users/{user_id}/role")
def update_user_role_api(user_id: int, data: UpdateUserRoleRequest):
    success, message = update_user_role(user_id, data.role)

    return {
        "success": success,
        "message": message
    }


@app.patch("/api/users/{user_id}/status")
def update_user_status_api(user_id: int, data: UpdateUserStatusRequest):
    success, message = update_user_status(user_id, data.status)

    return {
        "success": success,
        "message": message
    }


@app.post("/api/model-versions")
def create_model_version_api(data: CreateModelVersionRequest):
    success, message = create_model_version(
        data.version,
        data.model_name,
        data.model_path,
        data.description,
        data.access_scope,
        data.created_by
    )

    return {
        "success": success,
        "message": message
    }


@app.get("/api/model-versions")
def list_model_versions_api(include_disabled: bool = True):
    return {
        "success": True,
        "models": list_model_versions(include_disabled)
    }


@app.get("/api/model-versions/accessible")
def list_accessible_model_versions_api(username: str):
    return {
        "success": True,
        "models": list_accessible_model_versions(username)
    }


@app.patch("/api/model-versions/{model_version_id}")
def update_model_version_api(model_version_id: int, data: UpdateModelVersionRequest):
    success, message = update_model_version(
        model_version_id,
        data.version,
        data.model_name,
        data.model_path,
        data.description,
        data.status,
        data.access_scope
    )

    return {
        "success": success,
        "message": message
    }


@app.get("/api/model-versions/{model_version_id}/permissions")
def list_model_version_permissions_api(model_version_id: int):
    return {
        "success": True,
        "permissions": list_model_version_permissions(model_version_id)
    }


@app.post("/api/model-versions/{model_version_id}/permissions")
def grant_model_version_access_api(model_version_id: int, data: GrantModelAccessRequest):
    success, message = grant_model_version_access(
        model_version_id,
        data.user_id,
        data.granted_by
    )

    return {
        "success": success,
        "message": message
    }


@app.post("/api/model-versions/{model_version_id}/permissions/revoke")
def revoke_model_version_access_api(model_version_id: int, data: GrantModelAccessRequest):
    success, message = revoke_model_version_access(model_version_id, data.user_id)

    return {
        "success": success,
        "message": message
    }
