from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth.dependencies import get_current_user
from backend.core.responses import api_response
from backend.users.schemas import ChangePasswordRequest
from backend.users.service import change_password


router = APIRouter(prefix="/api/users", tags=["users"])


@router.patch("/me/password")
def change_password_api(
    data: ChangePasswordRequest,
    current_user=Depends(get_current_user),
):
    success, message = change_password(
        current_user["id"],
        data.old_password,
        data.new_password,
    )

    if not success:
        status_code = (
            status.HTTP_401_UNAUTHORIZED
            if message == "Old password is incorrect"
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=message)

    return api_response(True, message)
