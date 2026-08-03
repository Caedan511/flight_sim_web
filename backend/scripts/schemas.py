from typing import Literal, Optional

from pydantic import BaseModel, Field


class UpdateScriptRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[Literal["active", "disabled", "deleted"]] = None
    scope: Optional[Literal["private", "public"]] = None
