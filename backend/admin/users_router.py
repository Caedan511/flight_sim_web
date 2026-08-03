from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth.dependencies import get_current_admin
from backend.core.responses import api_response
from backend.users.schemas import (
    CreateUserRequest,
    ResetPasswordRequest,
    UpdateUserRoleRequest,
    UpdateUserStatusRequest,
)
from backend.users.service import (
    create_user,
    get_user_by_uid,
    get_user_by_username,
    list_users,
    public_user,
    public_users,
    reset_password_by_uid,
    update_user_role,
    update_user_status,
)


router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


@router.post("")
def create_user_api(data: CreateUserRequest, current_admin=Depends(get_current_admin)):
    success, message = create_user(data.username, data.password, data.role)

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return api_response(True, message)


@router.get("")
def list_users_api(current_admin=Depends(get_current_admin)):
    return api_response(
        True,
        "Users fetched successfully",
        {"users": public_users(list_users())},
    )


@router.get("/by-username/{username}")
def get_user_by_username_api(username: str, current_admin=Depends(get_current_admin)):
    user = get_user_by_username(username)

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

    return api_response(True, "User found", {"user": public_user(user)})


@router.get("/{uid}")
def get_user_api(uid: str, current_admin=Depends(get_current_admin)):
    user = get_user_by_uid(uid)

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

    return api_response(True, "User found", {"user": public_user(user)})


@router.patch("/{uid}/password")
def reset_user_password_api(
    uid: str,
    data: ResetPasswordRequest,
    current_admin=Depends(get_current_admin),
):
    success, message = reset_password_by_uid(uid, data.new_password)

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return api_response(True, message)


@router.patch("/{uid}/role")
def update_user_role_api(
    uid: str,
    data: UpdateUserRoleRequest,
    current_admin=Depends(get_current_admin),
):
    success, message = update_user_role(uid, data.role)

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return api_response(True, message)


@router.patch("/{uid}/status")
def update_user_status_api(
    uid: str,
    data: UpdateUserStatusRequest,
    current_admin=Depends(get_current_admin),
):
    success, message = update_user_status(uid, data.status)

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return api_response(True, message)
