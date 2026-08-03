from typing import Literal

from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    role: Literal["admin", "normal"] = "normal"


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)




class UpdateUserRoleRequest(BaseModel):
    role: Literal["admin", "normal"]


class UpdateUserStatusRequest(BaseModel):
    status: Literal["active", "disabled"]
