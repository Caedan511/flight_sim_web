from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from backend.auth.dependencies import get_current_user
from backend.core.responses import api_response
from backend.scripts.service import (
    create_script,
    get_accessible_script,
    get_script_file_path,
    list_accessible_scripts,
    public_script,
    public_scripts,
    soft_delete_script,
)


router = APIRouter(prefix="/api/scripts", tags=["scripts"])


@router.post("")
def upload_script_api(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    success, message, script = create_script(
        file,
        name,
        description,
        "private",
        current_user,
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return api_response(True, message, {"script": public_script(script)})


@router.get("")
def list_scripts_api(current_user=Depends(get_current_user)):
    return api_response(
        True,
        "Scripts fetched successfully",
        {"scripts": public_scripts(list_accessible_scripts(current_user["id"]))},
    )


@router.get("/{script_code}")
def get_script_api(script_code: str, current_user=Depends(get_current_user)):
    script = get_accessible_script(script_code, current_user["id"])

    if script is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script does not exist")

    return api_response(True, "Script found", {"script": public_script(script)})


@router.get("/{script_code}/download")
def download_script_api(script_code: str, current_user=Depends(get_current_user)):
    script = get_accessible_script(script_code, current_user["id"])

    if script is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script does not exist")

    path = get_script_file_path(script)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script file does not exist")

    return FileResponse(path, filename=script["original_filename"])


@router.delete("/{script_code}")
def delete_script_api(script_code: str, current_user=Depends(get_current_user)):
    success, message = soft_delete_script(script_code, current_user["id"])

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return api_response(True, message)
