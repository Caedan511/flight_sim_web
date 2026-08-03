from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth.dependencies import get_current_user
from backend.auth.schemas import LoginRequest
from backend.auth.service import authenticate_user
from backend.core.responses import api_response
from backend.core.security import create_access_token
from backend.users.service import public_user


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(data: LoginRequest):
    success, result = authenticate_user(data.username, data.password)

    if not success:
        status_code = (
            status.HTTP_403_FORBIDDEN
            if result == "Account is disabled"
            else status.HTTP_401_UNAUTHORIZED
        )
        raise HTTPException(status_code=status_code, detail=result)

    return api_response(
        True,
        "Login successful",
        {
            "token": create_access_token(result),
            "token_type": "bearer",
            "user": public_user(result),
        },
    )


@router.post("/logout")
def logout_api(current_user=Depends(get_current_user)):
    return api_response(True, "Logout successful")


@router.get("/me")
def get_me_api(current_user=Depends(get_current_user)):
    return api_response(
        True,
        "Current user fetched successfully",
        {"user": public_user(current_user)},
    )
