from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.auth.dependencies import get_current_admin, get_current_user
from backend.core.responses import api_response
from backend.models.schemas import (
    ModelPermissionRequest,
    UpdateModelVersionRequest,
)
from backend.models.service import (
    create_model_version,
    grant_model_version_access,
    list_accessible_model_versions,
    list_model_version_permissions,
    list_model_versions,
    public_model_permissions,
    public_model_versions,
    revoke_model_version_access,
    update_model_version,
)


router = APIRouter(prefix="/api/model-versions", tags=["model-versions"])


@router.get("/accessible")
def list_accessible_model_versions_api(current_user=Depends(get_current_user)):
    return api_response(
        True,
        "Accessible model versions fetched successfully",
        {"models": public_model_versions(list_accessible_model_versions(current_user))},
    )


@router.post("")
def create_model_version_api(
    version: str = Form(...),
    model_name: str = Form(...),
    description: Optional[str] = Form(None),
    access_scope: str = Form("private"),
    file: UploadFile = File(...),
    current_admin=Depends(get_current_admin),
):
    success, message = create_model_version(
        version,
        model_name,
        file,
        description,
        access_scope,
        current_admin["id"],
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return api_response(True, message)


@router.get("")
def list_model_versions_api(
    include_disabled: bool = True,
    current_admin=Depends(get_current_admin),
):
    return api_response(
        True,
        "Model versions fetched successfully",
        {"models": public_model_versions(list_model_versions(include_disabled))},
    )


@router.patch("/{version}")
def update_model_version_api(
    version: str,
    data: UpdateModelVersionRequest,
    current_admin=Depends(get_current_admin),
):
    success, message = update_model_version(
        version,
        data.version,
        data.model_name,
        data.description,
        data.status,
        data.access_scope,
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return api_response(True, message)


@router.get("/{version}/permissions")
def list_model_version_permissions_api(
    version: str,
    current_admin=Depends(get_current_admin),
):
    return api_response(
        True,
        "Model version permissions fetched successfully",
        {"permissions": public_model_permissions(list_model_version_permissions(version))},
    )


@router.post("/{version}/permissions")
def grant_model_version_access_api(
    version: str,
    data: ModelPermissionRequest,
    current_admin=Depends(get_current_admin),
):
    success, message = grant_model_version_access(
        version,
        data.user_uid,
        current_admin["id"],
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return api_response(True, message)


@router.post("/{version}/permissions/revoke")
def revoke_model_version_access_api(
    version: str,
    data: ModelPermissionRequest,
    current_admin=Depends(get_current_admin),
):
    success, message = revoke_model_version_access(version, data.user_uid)

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return api_response(True, message)
