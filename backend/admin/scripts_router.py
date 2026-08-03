from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.auth.dependencies import get_current_admin
from backend.core.responses import api_response
from backend.scripts.schemas import UpdateScriptRequest
from backend.scripts.service import (
    create_script,
    get_script_for_admin,
    list_all_scripts,
    public_script,
    public_scripts,
    update_script_for_admin,
)


router = APIRouter(prefix="/api/admin/scripts", tags=["admin-scripts"])


@router.post("")
def upload_public_script_api(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_admin=Depends(get_current_admin),
):
    success, message, script = create_script(
        file,
        name,
        description,
        "public",
        current_admin,
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return api_response(True, message, {"script": public_script(script)})


@router.get("")
def list_scripts_api(
    include_deleted: bool = False,
    current_admin=Depends(get_current_admin),
):
    return api_response(
        True,
        "Scripts fetched successfully",
        {"scripts": public_scripts(list_all_scripts(include_deleted))},
    )


@router.get("/{script_code}")
def get_script_api(script_code: str, current_admin=Depends(get_current_admin)):
    script = get_script_for_admin(script_code)

    if script is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script does not exist")

    return api_response(True, "Script found", {"script": public_script(script)})


@router.patch("/{script_code}")
def update_script_api(
    script_code: str,
    data: UpdateScriptRequest,
    current_admin=Depends(get_current_admin),
):
    success, message = update_script_for_admin(
        script_code,
        data.name,
        data.description,
        data.status,
        data.scope,
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return api_response(True, message)


@router.delete("/{script_code}")
def delete_script_api(script_code: str, current_admin=Depends(get_current_admin)):
    success, message = update_script_for_admin(script_code, status="deleted")

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return api_response(True, "Script deleted successfully")
