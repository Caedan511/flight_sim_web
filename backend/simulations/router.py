from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from backend.auth.dependencies import get_current_user
from backend.core.responses import api_response
from backend.simulations.flight_script import ScriptValidationError
from backend.simulations.schemas import SubmitSimulationRequest
from backend.simulations.service import SimulationService, SimulationServiceError


router = APIRouter(prefix="/api/simulations", tags=["simulations"])
simulation_service = SimulationService()


@router.post("")
def submit_simulation_api(
    data: SubmitSimulationRequest,
    current_user=Depends(get_current_user),
):
    try:
        task = simulation_service.submit(data, current_user)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ScriptValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{exc.path}: {exc}",
        ) from exc
    except SimulationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return api_response(True, "Simulation task queued", {"task": task.to_public_dict()})


@router.get("")
def list_simulations_api(current_user=Depends(get_current_user)):
    tasks = [task.to_public_dict() for task in simulation_service.list_tasks(current_user)]
    return api_response(True, "Simulation tasks fetched successfully", {"tasks": tasks})


@router.get("/{task_code}")
def get_simulation_status_api(task_code: str, current_user=Depends(get_current_user)):
    task = simulation_service.get_status(task_code, current_user)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation task does not exist")

    return api_response(True, "Simulation task found", {"task": task.to_public_dict()})


@router.get("/{task_code}/result")
def get_simulation_result_api(task_code: str, current_user=Depends(get_current_user)):
    result = simulation_service.get_result(task_code, current_user)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation task does not exist")

    return api_response(True, "Simulation result fetched successfully", {"result": result})


@router.get("/{task_code}/report")
def download_simulation_report_api(task_code: str, current_user=Depends(get_current_user)):
    path = simulation_service.report_path(task_code, current_user)
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation report does not exist")

    return FileResponse(path, filename=f"{task_code}_report.html", media_type="text/html")


@router.post("/{task_code}/cancel")
def cancel_simulation_api(task_code: str, current_user=Depends(get_current_user)):
    if not simulation_service.cancel(task_code, current_user):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Simulation task cannot be cancelled")

    return api_response(True, "Simulation cancellation requested")
