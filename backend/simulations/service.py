import csv
import json
import queue
import threading
import time
from pathlib import Path

from backend.core.config import Config
from backend.scripts.service import get_accessible_script, get_script_file_path
from backend.simulations.adapters import create_adapter
from backend.simulations.contracts import (
    ModelSpec,
    SimulationArtifact,
    SimulationRequest,
    TaskStatus,
)
from backend.simulations.flight_script import FlightScript, ScriptValidationError
from backend.simulations.repository import (
    create_task,
    get_task,
    get_user_task,
    list_user_tasks,
    mark_interrupted_tasks_failed,
    replace_artifacts,
    update_task,
)


class SimulationServiceError(ValueError):
    pass


def _load_script_data(script_code, current_user):
    script = get_accessible_script(script_code, current_user["id"])
    if script is None:
        raise FileNotFoundError("Script does not exist")

    path = get_script_file_path(script)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError("Script file does not exist")

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ScriptValidationError("Flight script file must be valid JSON", "$") from exc


def _default_model():
    model_type = Config.SIMULATION_DEFAULT_MODEL_TYPE
    if model_type == "python_mock":
        return ModelSpec(
            model_name="Default Python Mock",
            model_type="python_mock",
        )

    if model_type == "native":
        if not Config.SIMULATION_DEFAULT_MODEL_PATH:
            raise SimulationServiceError("SIMULATION_DEFAULT_MODEL_PATH is required for native simulation")

        model_path = Path(Config.SIMULATION_DEFAULT_MODEL_PATH).resolve()
        if Config.SIMULATION_ALLOWED_MODEL_ROOTS:
            allowed = False
            for root in Config.SIMULATION_ALLOWED_MODEL_ROOTS:
                try:
                    model_path.relative_to(root)
                    allowed = True
                    break
                except ValueError:
                    continue
            if not allowed:
                raise SimulationServiceError("Default simulation model path is outside allowed model roots")

        return ModelSpec(
            model_name="Default Native Model",
            model_type="native",
            model_path=str(model_path),
            interface_version="1.0",
        )

    raise SimulationServiceError(f"Unsupported default simulation model type: {model_type}")


class SimulationService:
    def __init__(self):
        self._queue = queue.Queue()
        self._requests = {}
        self._cancelled = set()
        self._lock = threading.RLock()

        mark_interrupted_tasks_failed()
        for index in range(Config.SIMULATION_WORKER_COUNT):
            threading.Thread(
                target=self._worker_loop,
                name=f"simulation-worker-{index + 1}",
                daemon=True,
            ).start()

    def submit(self, data, current_user):
        script_data = _load_script_data(data.script_code, current_user)
        flight_script = FlightScript.from_dict(script_data)
        model = _default_model()

        task = create_task(
            user_id=current_user["id"],
            user_uid=current_user["uid"],
            script_code=data.script_code,
            subject=flight_script.subject_name,
            model_name=model.model_name,
            report_template_code=data.report_template_code,
            output_parameters=list(data.output_parameters),
        )

        request = SimulationRequest(
            task_code=task.task_code,
            user_id=current_user["id"],
            user_uid=current_user["uid"],
            script_code=data.script_code,
            script_data=script_data,
            model=model,
            output_directory=task.output_directory,
            report_template_code=data.report_template_code,
            output_parameters=tuple(data.output_parameters),
            timeout_seconds=data.timeout_seconds,
        )

        try:
            task_path = Path(task.output_directory)
            (task_path / "results").mkdir(parents=True, exist_ok=True)
            (task_path / "reports").mkdir(exist_ok=True)
            (task_path / "request.json").write_text(
                json.dumps(request.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            update_task(
                task.task_code,
                status=TaskStatus.FAILED.value,
                message="Failed to prepare simulation output directory",
                error_message=str(exc),
                finished_at="NOW",
            )
            raise SimulationServiceError("Failed to prepare simulation output directory") from exc

        with self._lock:
            self._requests[task.task_code] = request
        self._queue.put(task.task_code)
        return get_task(task.task_code) or task

    def list_tasks(self, current_user):
        return list_user_tasks(current_user["id"])

    def get_status(self, task_code, current_user):
        return get_user_task(task_code, current_user["id"])

    def get_result(self, task_code, current_user):
        task = self.get_status(task_code, current_user)
        if task is None:
            return None

        summary_path = Path(task.output_directory) / "results" / "summary.json"
        if not summary_path.exists():
            return {
                "task": task.to_public_dict(),
                "points": [],
                "series": [],
                "errors": [],
            }

        result = json.loads(summary_path.read_text(encoding="utf-8"))
        result["task"] = task.to_public_dict()
        return result

    def report_path(self, task_code, current_user):
        task = self.get_status(task_code, current_user)
        if task is None:
            return None

        path = Path(task.output_directory) / "reports" / "report.html"
        return path if path.is_file() else None

    def cancel(self, task_code, current_user):
        task = self.get_status(task_code, current_user)
        if task is None:
            return False
        if TaskStatus(task.status).finished:
            return False

        with self._lock:
            self._cancelled.add(task.task_code)
        update_task(task.task_code, message="Cancellation requested")
        return True

    def _worker_loop(self):
        while True:
            task_code = self._queue.get()
            try:
                if self._is_cancelled(task_code):
                    self._finish_cancelled(task_code)
                else:
                    self._run_task(task_code)
            except Exception as exc:
                update_task(
                    task_code,
                    status=TaskStatus.FAILED.value,
                    message="Simulation task failed",
                    error_message=str(exc),
                    finished_at="NOW",
                )
            finally:
                with self._lock:
                    self._requests.pop(task_code, None)
                    self._cancelled.discard(task_code)
                self._queue.task_done()

    def _run_task(self, task_code):
        with self._lock:
            request = self._requests[task_code]

        flight_script = FlightScript.from_dict(request.script_data)
        adapter = create_adapter(request.model)
        task_path = Path(request.output_directory)
        started = time.monotonic()

        update_task(
            task_code,
            status=TaskStatus.RUNNING.value,
            started_at="NOW",
            message=f"Loading {adapter.name}",
        )

        point_summaries = []
        all_series = []
        errors = []
        artifacts = []
        failed_points = 0

        for index, point in enumerate(flight_script.test_points):
            if self._is_cancelled(task_code):
                self._finish_cancelled(task_code)
                return
            if time.monotonic() - started > request.timeout_seconds:
                raise TimeoutError(f"Simulation exceeded {request.timeout_seconds} seconds")

            update_task(task_code, message=f"Running {point.point_id}")
            try:
                rows = adapter.simulate(point)
                saved_rows = self._select_output_rows(rows, request.output_parameters)
                csv_path = task_path / "results" / f"{point.point_id}.csv"
                self._write_csv(csv_path, saved_rows)
                artifact = self._artifact(task_code, "simulation_data", csv_path)
                artifacts.append(artifact.to_dict())
                all_series.extend({"point_id": point.point_id, **row} for row in saved_rows)
                point_summaries.append(
                    {
                        "id": point.point_id,
                        "status": "success",
                        "samples": len(rows),
                        "max_altitude_m": max(row["altitude_m"] for row in rows),
                        "max_speed_kmh": max(row["speed_kmh"] for row in rows),
                    }
                )
            except Exception as exc:
                errors.append({"point_id": point.point_id, "message": str(exc)})
                point_summaries.append(
                    {"id": point.point_id, "status": "failed", "message": str(exc)}
                )
                failed_points += 1

            completed = index + 1
            update_task(
                task_code,
                failed_points=failed_points,
                progress=round(completed / len(flight_script.test_points) * 85),
            )

        result = {
            "subject": flight_script.subject_name,
            "script_code": request.script_code,
            "model": request.model.to_dict(),
            "points": point_summaries,
            "errors": errors,
            "series": all_series,
        }
        summary_path = task_path / "results" / "summary.json"
        summary_path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        artifacts.append(self._artifact(task_code, "result_summary", summary_path).to_dict())

        update_task(
            task_code,
            status=TaskStatus.REPORTING.value,
            progress=92,
            message="Generating simulation report",
        )
        current = get_task(task_code)
        if current is None:
            raise RuntimeError("Simulation task disappeared")

        success_points = len(point_summaries) - failed_points
        if success_points == 0:
            final_status = TaskStatus.FAILED
        elif failed_points:
            final_status = TaskStatus.SUCCEEDED_WITH_WARNINGS
        else:
            final_status = TaskStatus.SUCCEEDED

        report_path = task_path / "reports" / "report.html"
        report_path.write_text(
            build_task_report(current, final_status.value, result),
            encoding="utf-8",
        )
        artifacts.append(self._artifact(task_code, "report", report_path).to_dict())
        replace_artifacts(task_code, artifacts)
        update_task(
            task_code,
            status=final_status.value,
            progress=100,
            message=(
                "Simulation finished"
                if final_status == TaskStatus.SUCCEEDED
                else (
                    "Simulation finished with warnings"
                    if final_status == TaskStatus.SUCCEEDED_WITH_WARNINGS
                    else "Simulation failed"
                )
            ),
            finished_at="NOW",
        )

    def _is_cancelled(self, task_code):
        with self._lock:
            return task_code in self._cancelled

    @staticmethod
    def _finish_cancelled(task_code):
        update_task(
            task_code,
            status=TaskStatus.CANCELLED.value,
            message="Simulation task cancelled",
            finished_at="NOW",
        )

    @staticmethod
    def _select_output_rows(rows, output_parameters):
        if not rows:
            return []
        if not output_parameters:
            return rows

        available = set(rows[0])
        selected = ["time_s", *(name for name in output_parameters if name != "time_s")]
        unknown = set(selected) - available
        if unknown:
            raise ValueError(f"Unsupported output parameters: {', '.join(sorted(unknown))}")

        return [{key: row[key] for key in selected} for row in rows]

    @staticmethod
    def _write_csv(path, rows):
        with path.open("w", encoding="utf-8", newline="") as handle:
            fieldnames = list(rows[0]) if rows else ["time_s"]
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def _artifact(task_code, artifact_type, path):
        content_types = {
            ".csv": "text/csv",
            ".json": "application/json",
            ".html": "text/html",
        }
        return SimulationArtifact(
            artifact_code=f"{task_code}-{artifact_type}-{path.stem}",
            task_code=task_code,
            artifact_type=artifact_type,
            filename=path.name,
            file_path=str(path.resolve()),
            content_type=content_types.get(path.suffix.lower(), "application/octet-stream"),
        )


def build_task_report(task, final_status, result):
    from backend.simulations.report import build_report

    task_data = task.to_dict()
    task_data["status"] = final_status
    return build_report(task_data, result)
