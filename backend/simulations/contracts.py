from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    REPORTING = "reporting"
    SUCCEEDED = "succeeded"
    SUCCEEDED_WITH_WARNINGS = "succeeded_with_warnings"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def finished(self):
        return self in {
            TaskStatus.SUCCEEDED,
            TaskStatus.SUCCEEDED_WITH_WARNINGS,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        }


@dataclass(frozen=True)
class ModelSpec:
    model_name: str
    model_type: str
    model_path: str | None = None
    interface_version: str = "1.0"

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class SimulationRequest:
    task_code: str
    user_id: int
    user_uid: str
    script_code: str
    script_data: dict[str, Any]
    model: ModelSpec
    output_directory: str
    report_template_code: str = "standard"
    output_parameters: tuple[str, ...] = ()
    timeout_seconds: int = 3600

    def to_dict(self):
        value = asdict(self)
        value["output_parameters"] = list(self.output_parameters)
        return value


@dataclass
class SimulationArtifact:
    artifact_code: str
    task_code: str
    artifact_type: str
    filename: str
    file_path: str
    content_type: str

    def to_dict(self):
        return asdict(self)

    def to_public_dict(self):
        value = self.to_dict()
        value.pop("file_path", None)
        return value


@dataclass
class TaskRecord:
    id: int
    task_code: str
    user_id: int
    user_uid: str
    script_code: str
    subject: str
    model_name: str
    report_template_code: str
    output_parameters: list[str]
    output_directory: str
    status: str = TaskStatus.QUEUED.value
    progress: int = 0
    failed_points: int = 0
    message: str = "Simulation task queued"
    error_message: str | None = None
    submitted_at: Any = None
    started_at: Any = None
    finished_at: Any = None
    updated_at: Any = None
    artifacts: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    def to_public_dict(self):
        value = self.to_dict()
        value.pop("id", None)
        value.pop("user_id", None)
        value.pop("output_directory", None)
        value["artifacts"] = [
            {key: item for key, item in artifact.items() if key != "file_path"}
            for artifact in value["artifacts"]
        ]
        return value
