from typing import Literal, Optional

from pydantic import BaseModel, Field


class UpdateModelVersionRequest(BaseModel):
    version: Optional[str] = Field(None, min_length=1, max_length=50)
    model_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[Literal["active", "disabled"]] = None
    access_scope: Optional[Literal["private", "all_users"]] = None


class ModelPermissionRequest(BaseModel):
    user_uid: str = Field(..., min_length=1, max_length=20)
